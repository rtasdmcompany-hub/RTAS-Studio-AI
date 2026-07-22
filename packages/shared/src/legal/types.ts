export type LegalSection = {
  title: string;
  body: string;
  bullets?: readonly string[];
};

/** Shared metadata shown on every legal / policy page. */
export type LegalDocumentMeta = {
  /** Semantic document version (e.g. "1.1"). */
  version: string;
  /** Date the current version becomes effective. */
  effectiveDate: string;
  /** Date of the most recent editorial or substantive update. */
  lastUpdated: string;
};
