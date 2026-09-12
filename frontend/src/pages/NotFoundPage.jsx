import { Link } from "react-router-dom";
import { Compass } from "lucide-react";

export default function NotFoundPage() {
  return (
    <section className="content">
      <div className="page-heading">
        <div>
          <p className="breadcrumb">Home / Not found</p>
          <h2>Page not found</h2>
          <p className="subtitle">
            The page you were looking for doesn't exist or may have moved.
          </p>
        </div>
      </div>

      <div className="state-card">
        <Compass size={44} strokeWidth={1.5} />
        <span>
          Check the address or head back to the dashboard.
        </span>
        <Link
          to="/"
          className="primary-button"
          style={{ marginTop: 12, textDecoration: "none" }}
        >
          Back to dashboard
        </Link>
      </div>
    </section>
  );
}
