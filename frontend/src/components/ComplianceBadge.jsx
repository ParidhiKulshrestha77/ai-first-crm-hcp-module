import React from "react";

export default function ComplianceBadge({ flagged, notes }) {
  if (!flagged) return <span className="badge badge-clear">✔ Compliance clear</span>;
  return (
    <span className="badge badge-flag" title={notes || "Flagged for compliance review"}>
      ⚠ Needs review
    </span>
  );
}
