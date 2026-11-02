import Navbar from '../components/navbar/navbar.jsx'
import experiences from '../data/experience.js'

export default function ExperiencesPage() {
  return (
    <>
    <Navbar solid/>
      <main>
        {experiences.map((e) => (
          <section key={e.id}>
            <h2>{e.title}</h2>
            <img src={e.image} alt={e.title} />
            <p>{e.description}</p>
          </section>
        ))}
      </main>
    </>
  )
}