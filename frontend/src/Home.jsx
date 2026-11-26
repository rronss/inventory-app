import Hero from './Hero.jsx'

export default function Home() {
  return (
    <Hero>
      <a className="button" href="#/inventory">
        Go to inventory
      </a>
      <a className="button ghost" href="#/inventory/overview">
        View overview
      </a>
    </Hero>
  )
}
