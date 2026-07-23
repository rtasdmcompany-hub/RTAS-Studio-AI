import type { Metadata } from "next";
import { DMCA_INTRO, DMCA_SECTIONS, PRODUCT_NAME } from "@rtas/shared";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { LegalProse } from "@/components/legal/LegalProse";
import { StructuredData } from "@/components/seo/StructuredData";
import { buildPageMetadata } from "@/lib/site-metadata";
import { breadcrumbSchema } from "@/lib/structured-data";

export const metadata: Metadata = buildPageMetadata({
  title: "Copyright & DMCA",
  description: `Copyright and DMCA notice procedure for ${PRODUCT_NAME} — how to report alleged infringement.`,
  path: "/dmca",
  openGraphTitle: `Copyright & DMCA · ${PRODUCT_NAME}`,
  openGraphDescription: `Designated copyright contact and notice requirements for ${PRODUCT_NAME}.`,
});

export default function DmcaPage() {
  return (
    <LegalLayout
      title="Copyright & DMCA"
      subtitle="Notice-and-takedown process for alleged copyright infringement"
    >
      <StructuredData
        data={breadcrumbSchema([
          { name: "Home", path: "/" },
          { name: "Copyright & DMCA", path: "/dmca" },
        ])}
      />
      <LegalProse intro={DMCA_INTRO} sections={DMCA_SECTIONS} />
    </LegalLayout>
  );
}
