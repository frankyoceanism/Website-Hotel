import { useState } from 'react'
import { Link } from 'react-router'
import experiences from '../../data/experience'
import './experience.css'

function Experiences() {
  const [activeId, setActiveId] = useState(experiences[0].id)
  const active = experiences.find((e) => e.id === activeId)

  return (
    <section className="exp">
      <h2 className="exp__heading">More Ways to Enjoy Your Stay</h2>

      <div className="exp__tabs" role="tablist">
        {experiences.map((e) => (
          <button
            key={e.id}
            role="tab"
            aria-selected={e.id === activeId}
            className={`exp__tab ${e.id === activeId ? 'is-active' : ''}`}
            onClick={() => setActiveId(e.id)}
          >
            {e.tab}
          </button>
        ))}
      </div>

      <div className="exp__card">
        <img className="exp__image" src={active.image} alt={active.title} />
        <div className="exp__content">
          <span className="exp__label">{active.tab}</span>
          <h3 className="exp__title">{active.title}</h3>
          <p className="exp__desc">{active.description}</p>
          <Link to="/experiences" className="exp__link">
            Discover More
          </Link>
        </div>
      </div>
    </section>
  )
}

export default Experiences;