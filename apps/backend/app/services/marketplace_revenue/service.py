"""Marketplace Analytics, Revenue Intelligence & Monetization — Phase 9 Sprint 9."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from app.services.marketplace_revenue import store
from app.services.marketplace_revenue.catalog import (
    CATEGORIES,
    FORECAST_HORIZONS,
    PRODUCT_METRICS,
    REVENUE_STREAMS,
    SALE_EVENT_TYPES,
    growth_rate,
    marketplace_health_score,
    simple_forecast,
)
from app.services.marketplace_revenue.models import (
    CreatorStatsRecord,
    CustomerMetricRecord,
    FinancialSummaryRecord,
    ProductMetricRecord,
    RevenueForecastRecord,
    RevenueLedgerRecord,
    SalesEventRecord,
    new_id,
)
from app.services.marketplace_revenue.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _period(dt: datetime | None = None) -> str:
    d = dt or _now()
    return d.strftime("%Y-%m")


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action, actor_id=actor_id, success=True, detail=detail or action, metadata=meta
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _require_finance(*, actor_id: str, organization_id: str) -> None:
    """Revenue access control — org members with read; finance isolation via org scope."""
    _require_member(actor_id=actor_id, organization_id=organization_id)


class RevenueAnalyticsEngine:
    """Track gross/net revenue across subscription, marketplace, credits, refunds."""

    def record(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_finance(actor_id=actor_id, organization_id=org_id)
            stream = str(require_non_empty(payload.get("stream"), "stream"))
            if stream not in REVENUE_STREAMS:
                raise ValidationError(f"unknown revenue stream: {stream}")
            amount = float(payload.get("amount") or 0.0)
            if stream != "refund" and amount < 0:
                raise ValidationError("amount must be non-negative")
            if stream == "refund" and amount > 0:
                amount = -abs(amount)
            ws = payload.get("workspaceId")
            row = RevenueLedgerRecord(
                id=new_id("rev_"),
                organization_id=org_id,
                workspace_id=str(ws) if ws else None,
                stream=stream,
                amount=amount,
                currency=str(payload.get("currency") or "USD"),
                creator_id=(
                    str(payload["creatorId"]) if payload.get("creatorId") else None
                ),
                product_id=(
                    str(payload["productId"]) if payload.get("productId") else None
                ),
                customer_id=(
                    str(payload["customerId"]) if payload.get("customerId") else None
                ),
                period=str(payload.get("period") or _period()),
                metadata=dict(payload.get("metadata") or {}),
            )
            store.save_ledger(row)
            _audit(
                "marketplace_revenue.ledger_recorded",
                actor_id,
                stream,
                organizationId=org_id,
                amount=amount,
            )
            return {"ok": True, "entry": row.to_dict()}

    def report(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        period: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_finance(actor_id=actor_id, organization_id=organization_id)
            rows = store.list_ledger(
                organization_id=organization_id,
                workspace_id=workspace_id,
                period=period,
            )
            by_stream: dict[str, float] = {s: 0.0 for s in REVENUE_STREAMS}
            monthly: dict[str, float] = defaultdict(float)
            annual: dict[str, float] = defaultdict(float)
            for r in rows:
                by_stream[r.stream] = by_stream.get(r.stream, 0.0) + r.amount
                monthly[r.period] += r.amount if r.stream != "refund" else 0.0
                year = r.period[:4] if r.period else ""
                if year:
                    annual[year] += r.amount if r.stream != "refund" else 0.0

            subscription = by_stream.get("subscription", 0.0)
            marketplace = by_stream.get("marketplace", 0.0)
            credit_sales = by_stream.get("credit_sales", 0.0)
            refund_raw = by_stream.get("refund", 0.0)
            refund_amount = abs(refund_raw)
            gross = subscription + marketplace + credit_sales
            net = gross - refund_amount
            total = net

            current_period = period or _period()
            monthly_revenue = monthly.get(current_period, 0.0)
            year_key = current_period[:4]
            annual_revenue = annual.get(year_key, 0.0)

            summary = FinancialSummaryRecord(
                id=new_id("fin_"),
                organization_id=organization_id,
                period=current_period,
                gross_revenue=gross,
                refund_amount=refund_amount,
                net_revenue=net,
                subscription_revenue=subscription,
                marketplace_revenue=marketplace,
                credit_sales_revenue=credit_sales,
            )
            store.save_summary(summary)
            _audit(
                "marketplace_revenue.revenue_report",
                actor_id,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "workspaceId": workspace_id,
                "period": current_period,
                "totalRevenue": round(total, 2),
                "monthlyRevenue": round(monthly_revenue, 2),
                "annualRevenue": round(annual_revenue, 2),
                "subscriptionRevenue": round(subscription, 2),
                "marketplaceRevenue": round(marketplace, 2),
                "creditSalesRevenue": round(credit_sales, 2),
                "refundAmount": round(refund_amount, 2),
                "netRevenue": round(net, 2),
                "grossRevenue": round(gross, 2),
                "monthlyBreakdown": {k: round(v, 2) for k, v in sorted(monthly.items())},
                "annualBreakdown": {k: round(v, 2) for k, v in sorted(annual.items())},
                "summary": summary.to_dict(),
                "entryCount": len(rows),
            }


class SalesIntelligenceEngine:
    """Sales events, conversion, and growth trends."""

    def record(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_finance(actor_id=actor_id, organization_id=org_id)
            event_type = str(require_non_empty(payload.get("eventType"), "eventType"))
            if event_type not in SALE_EVENT_TYPES:
                raise ValidationError(f"unknown sale event: {event_type}")
            amount = float(payload.get("amount") or 0.0)
            ws = payload.get("workspaceId")
            row = SalesEventRecord(
                id=new_id("sale_"),
                organization_id=org_id,
                workspace_id=str(ws) if ws else None,
                event_type=event_type,
                amount=amount,
                product_id=(
                    str(payload["productId"]) if payload.get("productId") else None
                ),
                creator_id=(
                    str(payload["creatorId"]) if payload.get("creatorId") else None
                ),
                customer_id=(
                    str(payload["customerId"]) if payload.get("customerId") else None
                ),
                quantity=int(payload.get("quantity") or 1),
            )
            store.save_sale(row)

            # Mirror into revenue ledger for stream mapping
            stream_map = {
                "purchase": "marketplace",
                "subscription": "subscription",
                "credit_pack": "credit_sales",
                "refund": "refund",
            }
            RevenueAnalyticsEngine().record(
                {
                    "organizationId": org_id,
                    "workspaceId": ws,
                    "stream": stream_map[event_type],
                    "amount": amount,
                    "productId": payload.get("productId"),
                    "creatorId": payload.get("creatorId"),
                    "customerId": payload.get("customerId"),
                },
                actor_id=actor_id,
            )

            if payload.get("customerId") and event_type != "refund":
                MonetizationEngine()._touch_customer(
                    org_id, str(payload["customerId"]), amount
                )
            if payload.get("creatorId") and event_type in ("purchase", "subscription"):
                CreatorRevenueEngine()._credit_sale(
                    org_id,
                    str(payload["creatorId"]),
                    amount,
                    downloads=0,
                )

            _audit(
                "marketplace_revenue.sale_recorded",
                actor_id,
                event_type,
                organizationId=org_id,
            )
            return {"ok": True, "sale": row.to_dict()}

    def report(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_finance(actor_id=actor_id, organization_id=organization_id)
            rows = store.list_sales(
                organization_id=organization_id, workspace_id=workspace_id
            )
            by_type: dict[str, float] = {t: 0.0 for t in SALE_EVENT_TYPES}
            count_by_type: dict[str, int] = {t: 0 for t in SALE_EVENT_TYPES}
            total = 0.0
            for r in rows:
                by_type[r.event_type] = by_type.get(r.event_type, 0.0) + r.amount
                count_by_type[r.event_type] = count_by_type.get(r.event_type, 0) + 1
                if r.event_type != "refund":
                    total += r.amount

            # Growth: compare first half vs second half of events by amount
            non_refund = [r for r in rows if r.event_type != "refund"]
            mid = max(1, len(non_refund) // 2)
            first = sum(r.amount for r in non_refund[:mid])
            second = sum(r.amount for r in non_refund[mid:])
            sales_growth = growth_rate(second, first) if non_refund else 0.0

            _audit(
                "marketplace_revenue.sales_report",
                actor_id,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "workspaceId": workspace_id,
                "totalSales": round(total, 2),
                "salesCount": len(non_refund),
                "refundCount": count_by_type.get("refund", 0),
                "byEventType": {k: round(v, 2) for k, v in by_type.items()},
                "countByEventType": count_by_type,
                "salesGrowth": sales_growth,
                "salesForecast": simple_forecast(
                    [r.amount for r in non_refund[-6:]] or [total], periods=3
                ),
                "events": [r.to_dict() for r in rows[-50:]],
            }


class MarketplaceInsightsEngine:
    """Best sellers, trending, featured, category & search performance."""

    def track(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            product_id = str(require_non_empty(payload.get("productId"), "productId"))
            metric = str(require_non_empty(payload.get("metric"), "metric"))
            if metric not in PRODUCT_METRICS:
                raise ValidationError(f"unknown product metric: {metric}")
            category = str(payload.get("category") or "other")
            if category not in CATEGORIES:
                category = "other"
            row = ProductMetricRecord(
                id=new_id("pm_"),
                organization_id=org_id,
                product_id=product_id,
                metric=metric,
                category=category,
                featured=bool(payload.get("featured")),
                value=float(payload.get("value") or 1.0),
            )
            store.save_product_metric(row)

            if payload.get("creatorId"):
                creator = CreatorRevenueEngine()
                if metric == "download":
                    creator._credit_sale(
                        org_id, str(payload["creatorId"]), 0.0, downloads=1
                    )
                elif metric == "view":
                    creator._add_view(org_id, str(payload["creatorId"]))
                elif metric == "purchase":
                    creator._credit_sale(
                        org_id,
                        str(payload["creatorId"]),
                        float(payload.get("amount") or 0.0),
                        downloads=0,
                    )

            _audit(
                "marketplace_revenue.product_metric",
                actor_id,
                metric,
                organizationId=org_id,
                productId=product_id,
            )
            return {"ok": True, "metric": row.to_dict()}

    def report(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            rows = store.list_product_metrics(organization_id=organization_id)
            views: dict[str, float] = defaultdict(float)
            downloads: dict[str, float] = defaultdict(float)
            purchases: dict[str, float] = defaultdict(float)
            search: dict[str, float] = defaultdict(float)
            category_perf: dict[str, float] = defaultdict(float)
            featured: set[str] = set()
            product_category: dict[str, str] = {}

            for r in rows:
                product_category[r.product_id] = r.category
                if r.featured:
                    featured.add(r.product_id)
                if r.metric == "view":
                    views[r.product_id] += r.value
                elif r.metric == "download":
                    downloads[r.product_id] += r.value
                elif r.metric == "purchase":
                    purchases[r.product_id] += r.value
                    category_perf[r.category] += r.value
                elif r.metric == "search_impression":
                    search[r.product_id] += r.value
                elif r.metric == "feature":
                    featured.add(r.product_id)

            def _top(d: dict[str, float], n: int = 10) -> list[dict[str, Any]]:
                ranked = sorted(d.items(), key=lambda x: x[1], reverse=True)[:n]
                return [
                    {
                        "productId": pid,
                        "value": round(val, 2),
                        "category": product_category.get(pid, "other"),
                    }
                    for pid, val in ranked
                ]

            # Trending = purchase velocity weighted with recent views
            trend_score = {
                pid: purchases.get(pid, 0) * 3 + views.get(pid, 0)
                for pid in set(views) | set(purchases)
            }

            total_views = sum(views.values())
            total_downloads = sum(downloads.values())
            total_purchases = sum(purchases.values())
            conversion = (
                round((total_purchases / total_views) * 100.0, 2) if total_views else 0.0
            )

            _audit(
                "marketplace_revenue.marketplace_report",
                actor_id,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "bestSellingProducts": _top(purchases),
                "trendingProducts": _top(trend_score),
                "featuredProducts": sorted(featured),
                "categoryPerformance": {
                    k: round(v, 2) for k, v in sorted(category_perf.items())
                },
                "searchPerformance": _top(search),
                "productViews": round(total_views, 2),
                "productDownloads": round(total_downloads, 2),
                "productPurchases": round(total_purchases, 2),
                "conversionRate": conversion,
                "products": [
                    {
                        "productId": pid,
                        "views": round(views.get(pid, 0), 2),
                        "downloads": round(downloads.get(pid, 0), 2),
                        "purchases": round(purchases.get(pid, 0), 2),
                        "category": product_category.get(pid, "other"),
                        "featured": pid in featured,
                    }
                    for pid in sorted(set(views) | set(downloads) | set(purchases))
                ],
            }


class CreatorRevenueEngine:
    """Creator earnings, ratings, conversion, top assets, growth."""

    def _ensure(self, org_id: str, creator_id: str) -> CreatorStatsRecord:
        existing = store.get_creator(org_id, creator_id)
        if existing:
            return existing
        row = CreatorStatsRecord(
            id=new_id("cr_"),
            organization_id=org_id,
            creator_id=creator_id,
        )
        store.save_creator(row)
        return row

    def _credit_sale(
        self, org_id: str, creator_id: str, amount: float, downloads: int = 0
    ) -> None:
        row = self._ensure(org_id, creator_id)
        row.revenue += amount
        if amount > 0:
            row.sales += 1
        row.downloads += downloads
        row.updated_at = _now()
        store.save_creator(row)

    def _add_view(self, org_id: str, creator_id: str) -> None:
        row = self._ensure(org_id, creator_id)
        row.views += 1
        row.updated_at = _now()
        store.save_creator(row)

    def rate(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            creator_id = str(require_non_empty(payload.get("creatorId"), "creatorId"))
            rating = float(payload.get("rating") or 0.0)
            if rating < 1 or rating > 5:
                raise ValidationError("rating must be between 1 and 5")
            row = self._ensure(org_id, creator_id)
            row.rating_total += rating
            row.rating_count += 1
            row.review_count += 1
            row.updated_at = _now()
            store.save_creator(row)
            _audit(
                "marketplace_revenue.creator_rated",
                actor_id,
                creator_id,
                organizationId=org_id,
            )
            return {"ok": True, "creator": row.to_dict()}

    def report(
        self,
        *,
        actor_id: str,
        organization_id: str,
        creator_id: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            creators = store.list_creators(organization_id=organization_id)
            if creator_id:
                creators = [c for c in creators if c.creator_id == creator_id]

            # Top performing assets from product metrics linked via sales
            sales = store.list_sales(organization_id=organization_id)
            asset_rev: dict[str, float] = defaultdict(float)
            for s in sales:
                if s.product_id and s.event_type == "purchase":
                    if creator_id is None or s.creator_id == creator_id:
                        asset_rev[s.product_id] += s.amount
            top_assets = [
                {"productId": pid, "revenue": round(v, 2)}
                for pid, v in sorted(
                    asset_rev.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            payloads = [c.to_dict() for c in creators]
            total_rev = sum(c.revenue for c in creators)
            # Growth: compare creator revenue halves if multiple
            revs = [c.revenue for c in creators]
            mid = max(1, len(revs) // 2)
            growth = (
                growth_rate(sum(revs[mid:]), sum(revs[:mid])) if revs else 0.0
            )

            _audit(
                "marketplace_revenue.creator_report",
                actor_id,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "creatorRevenue": round(total_rev, 2),
                "productSales": sum(c.sales for c in creators),
                "downloads": sum(c.downloads for c in creators),
                "conversionRate": round(
                    (
                        sum(c.sales for c in creators)
                        / max(1, sum(c.views for c in creators))
                    )
                    * 100.0,
                    2,
                )
                if any(c.views for c in creators)
                else 0.0,
                "averageRating": round(
                    sum(c.rating_total for c in creators)
                    / max(1, sum(c.rating_count for c in creators)),
                    2,
                )
                if any(c.rating_count for c in creators)
                else 0.0,
                "reviewStatistics": {
                    "reviewCount": sum(c.review_count for c in creators),
                    "ratingCount": sum(c.rating_count for c in creators),
                },
                "topPerformingAssets": top_assets,
                "revenueGrowth": growth,
                "creators": payloads,
            }


class RevenueForecastEngine:
    """Revenue / sales forecasts, growth trends, marketplace health."""

    def forecast(
        self,
        *,
        actor_id: str,
        organization_id: str,
        horizon: str = "90d",
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            _require_finance(actor_id=actor_id, organization_id=organization_id)
            if horizon not in FORECAST_HORIZONS:
                raise ValidationError(f"unknown horizon: {horizon}")
            periods_map = {"30d": 1, "90d": 3, "180d": 6, "365d": 12}
            periods = periods_map[horizon]

            ledger = store.list_ledger(organization_id=organization_id)
            monthly: dict[str, float] = defaultdict(float)
            for r in ledger:
                if r.stream == "refund":
                    continue
                monthly[r.period] += r.amount
            history = [monthly[k] for k in sorted(monthly.keys())]
            projected = simple_forecast(history, periods=periods)
            baseline = history[-1] if history else 0.0
            prev = history[-2] if len(history) > 1 else baseline
            g = growth_rate(baseline, prev)

            row = RevenueForecastRecord(
                id=new_id("fc_"),
                organization_id=organization_id,
                horizon=horizon,
                projected=projected,
                baseline=baseline,
                growth_rate=g,
            )
            store.save_forecast(row)

            sales = store.list_sales(organization_id=organization_id)
            sale_amounts = [
                s.amount for s in sales if s.event_type != "refund"
            ]
            sales_forecast = simple_forecast(
                sale_amounts[-6:] or ([sum(sale_amounts)] if sale_amounts else [0.0]),
                periods=min(3, periods),
            )

            customers = store.list_customers(organization_id=organization_id)
            churned = sum(1 for c in customers if c.churned)
            churn_rate = (
                round((churned / len(customers)) * 100.0, 2) if customers else 0.0
            )
            marketplace = MarketplaceInsightsEngine().report(
                actor_id=actor_id, organization_id=organization_id
            )
            creators = store.list_creators(organization_id=organization_id)
            avg_rating = (
                sum(c.rating_total for c in creators)
                / max(1, sum(c.rating_count for c in creators))
                if any(c.rating_count for c in creators)
                else 4.0
            )
            health = marketplace_health_score(
                conversion_rate=float(marketplace.get("conversionRate") or 0.0),
                avg_rating=avg_rating,
                churn_rate=churn_rate,
                revenue_growth=g,
            )

            _audit(
                "marketplace_revenue.forecast",
                actor_id,
                horizon,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "horizon": horizon,
                "revenueForecast": projected,
                "salesForecast": sales_forecast,
                "growthTrends": {
                    "revenueGrowth": g,
                    "baseline": round(baseline, 2),
                    "history": [round(h, 2) for h in history],
                },
                "marketplaceHealthScore": health,
                "forecast": row.to_dict(),
            }


class MonetizationEngine:
    """Customer LTV, ARPU, churn, retention, marketplace health BI."""

    def _touch_customer(
        self, org_id: str, customer_id: str, amount: float
    ) -> CustomerMetricRecord:
        row = store.get_customer(org_id, customer_id)
        if row is None:
            row = CustomerMetricRecord(
                id=new_id("cust_"),
                organization_id=org_id,
                customer_id=customer_id,
                total_spend=amount,
                purchases=1 if amount > 0 else 0,
            )
        else:
            row.total_spend += amount
            if amount > 0:
                row.purchases += 1
            row.last_seen_at = _now()
            row.churned = False
        store.save_customer(row)
        return row

    def mark_churn(
        self, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_finance(actor_id=actor_id, organization_id=org_id)
            customer_id = str(
                require_non_empty(payload.get("customerId"), "customerId")
            )
            row = store.get_customer(org_id, customer_id)
            ForbiddenError, NotFoundError = _auth_errors()
            if row is None:
                raise NotFoundError("customer metrics not found")
            row.churned = True
            store.save_customer(row)
            _audit(
                "marketplace_revenue.customer_churned",
                actor_id,
                customer_id,
                organizationId=org_id,
            )
            return {"ok": True, "customer": row.to_dict()}

    def customers(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_finance(actor_id=actor_id, organization_id=organization_id)
            rows = store.list_customers(organization_id=organization_id)
            active = [c for c in rows if not c.churned]
            churned = [c for c in rows if c.churned]
            active_spend = sum(c.total_spend for c in active)
            arpu = round(active_spend / len(active), 2) if active else 0.0
            clv = arpu
            # Retention = active / total
            retention = (
                round((len(active) / len(rows)) * 100.0, 2) if rows else 100.0
            )
            churn_rate = (
                round((len(churned) / len(rows)) * 100.0, 2) if rows else 0.0
            )

            marketplace = MarketplaceInsightsEngine().report(
                actor_id=actor_id, organization_id=organization_id
            )
            creators = store.list_creators(organization_id=organization_id)
            avg_rating = (
                sum(c.rating_total for c in creators)
                / max(1, sum(c.rating_count for c in creators))
                if any(c.rating_count for c in creators)
                else 4.0
            )
            rev = RevenueAnalyticsEngine().report(
                actor_id=actor_id, organization_id=organization_id
            )
            history_vals = list(rev.get("monthlyBreakdown", {}).values())
            g = (
                growth_rate(history_vals[-1], history_vals[-2])
                if len(history_vals) >= 2
                else 0.0
            )
            health = marketplace_health_score(
                conversion_rate=float(marketplace.get("conversionRate") or 0.0),
                avg_rating=avg_rating,
                churn_rate=churn_rate,
                revenue_growth=g,
            )

            _audit(
                "marketplace_revenue.customer_metrics",
                actor_id,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "customerRetention": retention,
                "customerLifetimeValue": clv,
                "churnRate": churn_rate,
                "averageRevenuePerUser": arpu,
                "marketplaceHealthScore": health,
                "activeCustomers": len(active),
                "churnedCustomers": len(churned),
                "customers": [c.to_dict() for c in rows],
            }

    def products(
        self, *, actor_id: str, organization_id: str
    ) -> dict[str, Any]:
        """Product performance BI surface."""
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            marketplace = MarketplaceInsightsEngine().report(
                actor_id=actor_id, organization_id=organization_id
            )
            _audit(
                "marketplace_revenue.product_performance",
                actor_id,
                organizationId=organization_id,
            )
            return {
                "ok": True,
                "organizationId": organization_id,
                "bestSellingProducts": marketplace["bestSellingProducts"],
                "trendingProducts": marketplace["trendingProducts"],
                "featuredProducts": marketplace["featuredProducts"],
                "categoryPerformance": marketplace["categoryPerformance"],
                "searchPerformance": marketplace["searchPerformance"],
                "productViews": marketplace["productViews"],
                "productDownloads": marketplace["productDownloads"],
                "productPurchases": marketplace["productPurchases"],
                "products": marketplace["products"],
            }


class MarketplaceRevenueFacade:
    """Facade combining all six monetization / analytics engines."""

    def __init__(self) -> None:
        self.revenue = RevenueAnalyticsEngine()
        self.sales = SalesIntelligenceEngine()
        self.marketplace = MarketplaceInsightsEngine()
        self.creators = CreatorRevenueEngine()
        self.forecast = RevenueForecastEngine()
        self.monetization = MonetizationEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "revenueAnalytics": "ready",
                "salesIntelligence": "ready",
                "marketplaceInsights": "ready",
                "creatorRevenue": "ready",
                "revenueForecast": "ready",
                "monetization": "ready",
            },
            "revenueStreams": list(REVENUE_STREAMS),
            "saleEventTypes": list(SALE_EVENT_TYPES),
            "productMetrics": list(PRODUCT_METRICS),
            "forecastHorizons": list(FORECAST_HORIZONS),
            "stats": store.metrics(),
        }


_service: MarketplaceRevenueFacade | None = None


def get_marketplace_revenue_service() -> MarketplaceRevenueFacade:
    global _service
    if _service is None:
        _service = MarketplaceRevenueFacade()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_marketplace_revenue_service
