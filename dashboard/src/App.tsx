import { ClaimPage } from "./pages/ClaimPage";
import { InstructionsPage } from "./pages/InstructionsPage";
import { QueuePage } from "./pages/QueuePage";
import { useHash } from "./hooks";

function pageFor(hash: string) {
  const claim = /^#\/claims\/(.+)$/.exec(hash);
  if (claim) {
    return <ClaimPage key={claim[1]} claimId={claim[1]} />;
  }
  if (hash === "#/instructions") {
    return <InstructionsPage />;
  }
  return <QueuePage />;
}

export function App() {
  const hash = useHash();
  return (
    <>
      <header className="top">
        <a className="brand" href="#/claims">
          UnderCover
        </a>
        <nav>
          <a href="#/claims">Queue</a>
          <a href="#/instructions">Agent instructions</a>
        </nav>
      </header>
      <main>{pageFor(hash)}</main>
    </>
  );
}
