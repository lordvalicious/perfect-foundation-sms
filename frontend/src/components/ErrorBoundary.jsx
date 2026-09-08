import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error.message || String(error) };
  }

  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <section className="content">
          <div className="state-card error">
            <strong>Something went wrong</strong>
            <span>
              An unexpected error occurred while rendering this page.
            </span>
            <code style={{ display: "block", margin: "8px 0", fontSize: 12 }}>
              {this.state.message}
            </code>
            <span>
              The error has been logged to the browser console. If this keeps
              happening, contact your school administrator.
            </span>
            <button
              type="button"
              className="primary-button"
              onClick={() => window.location.reload()}
            >
              Reload page
            </button>
          </div>
        </section>
      );
    }
    return this.props.children;
  }
}