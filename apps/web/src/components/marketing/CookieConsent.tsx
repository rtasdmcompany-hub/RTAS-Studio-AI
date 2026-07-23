"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@rtas/ui";
import {
  COOKIE_PREFS_OPEN_EVENT,
  DEFAULT_ACCEPT_ALL,
  DEFAULT_NECESSARY_ONLY,
  readCookieConsent,
  writeCookieConsent,
  type CookieCategoryPrefs,
} from "@/lib/analytics";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [manage, setManage] = useState(false);
  const [draft, setDraft] = useState<CookieCategoryPrefs>(DEFAULT_NECESSARY_ONLY);

  useEffect(() => {
    const existing = readCookieConsent();
    if (!existing) setVisible(true);
    else setDraft(existing);

    const onOpen = () => {
      const current = readCookieConsent() ?? DEFAULT_NECESSARY_ONLY;
      setDraft(current);
      setManage(true);
      setVisible(true);
    };
    window.addEventListener(COOKIE_PREFS_OPEN_EVENT, onOpen);
    return () => window.removeEventListener(COOKIE_PREFS_OPEN_EVENT, onOpen);
  }, []);

  const save = (prefs: CookieCategoryPrefs) => {
    writeCookieConsent(prefs);
    setDraft(prefs);
    setManage(false);
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="rtas-cookie" role="dialog" aria-label="Cookie preferences">
      <div className="rtas-cookie__panel">
        {!manage ? (
          <>
            <p className="rtas-cookie__text">
              We use Necessary cookies for sign-in and studio preferences. Optional
              Analytics and Marketing help us measure performance and campaigns —
              only after you opt in. See our{" "}
              <Link href="/cookies">Cookie Policy</Link>.
            </p>
            <div className="rtas-cookie__actions">
              <Button
                variant="ghost"
                size="sm"
                className="rtas-cookie__btn"
                onClick={() => setManage(true)}
              >
                Manage preferences
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="rtas-cookie__btn"
                onClick={() => save(DEFAULT_NECESSARY_ONLY)}
              >
                Necessary only
              </Button>
              <Button
                variant="lavender"
                size="sm"
                className="rtas-cookie__btn"
                onClick={() => save(DEFAULT_ACCEPT_ALL)}
              >
                Accept all
              </Button>
            </div>
          </>
        ) : (
          <>
            <p className="rtas-cookie__text">
              Choose categories. Necessary cookies stay on so the Service works.
              You can change this anytime from Privacy settings or Cookie settings.
            </p>
            <ul className="rtas-cookie__cats">
              <li className="rtas-cookie__cat">
                <label>
                  <input type="checkbox" checked disabled readOnly />
                  <span>
                    <strong>Necessary</strong> — auth, security, consent storage
                  </span>
                </label>
              </li>
              <li className="rtas-cookie__cat">
                <label>
                  <input
                    type="checkbox"
                    checked={draft.analytics}
                    onChange={(e) =>
                      setDraft({ ...draft, analytics: e.target.checked })
                    }
                  />
                  <span>
                    <strong>Analytics</strong> — product and performance measurement
                  </span>
                </label>
              </li>
              <li className="rtas-cookie__cat">
                <label>
                  <input
                    type="checkbox"
                    checked={draft.marketing}
                    onChange={(e) =>
                      setDraft({ ...draft, marketing: e.target.checked })
                    }
                  />
                  <span>
                    <strong>Marketing</strong> — campaign tags when configured
                  </span>
                </label>
              </li>
            </ul>
            <div className="rtas-cookie__actions">
              <Button
                variant="ghost"
                size="sm"
                className="rtas-cookie__btn"
                onClick={() => {
                  if (readCookieConsent()) setVisible(false);
                  setManage(false);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="lavender"
                size="sm"
                className="rtas-cookie__btn"
                onClick={() => save({ ...draft, necessary: true })}
              >
                Save preferences
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
