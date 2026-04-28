import type { AnalysisResponse } from "@/lib/micromarket-types";

type NoticesProps = {
  activeAnalysis: AnalysisResponse | null;
  excludedEvidenceCount: number;
  workspaceError: string | null;
};

export function DashboardNotices({
  activeAnalysis,
  excludedEvidenceCount,
  workspaceError
}: NoticesProps) {
  return (
    <>
      {workspaceError ? (
        <section className="notice-panel error" aria-live="polite">
          {workspaceError}
        </section>
      ) : null}

      {activeAnalysis?.status === "failed" ? (
        <section className="notice-panel error" aria-live="polite">
          This analysis failed during processing. Its lineage is still visible, but forecast and
          sentiment outputs may be incomplete.
        </section>
      ) : null}

      {excludedEvidenceCount > 0 ? (
        <section className="notice-panel warning" aria-live="polite">
          {excludedEvidenceCount} article{excludedEvidenceCount === 1 ? "" : "s"} in the selected
          run {excludedEvidenceCount === 1 ? "was" : "were"} preserved for lineage but excluded
          from sentiment and forecast inputs.
        </section>
      ) : null}
    </>
  );
}
