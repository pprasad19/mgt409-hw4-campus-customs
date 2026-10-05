import { Link } from 'react-router-dom'

export default function About() {
  return (
    <div className="page prose-page">
      <header className="page-head">
        <span className="eyebrow">About Us</span>
        <h1>We print for the people who live here.</h1>
        <p className="lede">
          Campus Customs started in a basement on Elm Street with one heat press, a borrowed
          folding table, and a stack of blank crewnecks nobody had claimed yet. The idea was
          simple and it has not really changed: make the sweatshirt people actually want to wear,
          and sell it at a price a student can say yes to.
        </p>
      </header>

      <section className="prose-section">
        <h2>What we make</h2>
        <p>
          Hoodies, crewnecks, quarter-zips, tees, and the kind of fleece jacket that survives a
          walk across Cross Campus in February. We cut for comfort over trend, which means a
          little room in the shoulders and a collar that holds its shape past the first wash. Our
          graphics run from the plain navy wordmark to the vintage bulldog that keeps getting
          asked for by people who swear they saw it on their parent in an old photo.
        </p>
        <p>
          We cover the whole map of campus. Every residential college. Every varsity team, from
          the ones that fill the stands to the ones whose families are the stands. The graduate
          and professional schools too, because the Divinity crowd deserves a good fleece as much
          as anybody.
        </p>
      </section>

      <section className="prose-section">
        <h2>How we price</h2>
        <p>
          Everything in the shop sits between the cost of a decent lunch and the cost of a used
          textbook. That is deliberate. A sweatshirt that marks four years of your life should
          not be a budgeting decision you lose sleep over. We keep the runs small, the margins
          modest, and the price on the tag the same price you pay.
        </p>
      </section>

      <section className="prose-section">
        <h2>Who we are for</h2>
        <p>
          The first-year who needs one warm thing by October. The senior buying the crewneck they
          meant to buy sophomore year. The parent in another state who wants to feel close to a
          campus they have visited twice. The alum who has been gone a decade and still reaches
          for navy on a Saturday in the fall. We have made something for all of them, usually
          because one of them asked.
        </p>
      </section>

      <section className="prose-section">
        <h2>Finding things</h2>
        <p>
          The catalogue is searchable by color, team, college, and the kind of half-remembered
          description people actually use - <em>the gray one with the two helmets</em>, or{' '}
          <em>that navy quarter-zip my roommate has</em>. If browsing is not getting you there,
          the chat window in the corner is there to help you narrow it down.
        </p>
        <Link to="/products" className="btn btn-primary btn-lg">
          Browse the catalogue
        </Link>
      </section>

      <aside className="about-facts">
        <div>
          <strong>102</strong>
          <span>products in the shop</span>
        </div>
        <div>
          <strong>XS&ndash;XXL</strong>
          <span>every style, every size</span>
        </div>
        <div>
          <strong>New Haven</strong>
          <span>printed a few blocks from campus</span>
        </div>
      </aside>
    </div>
  )
}
