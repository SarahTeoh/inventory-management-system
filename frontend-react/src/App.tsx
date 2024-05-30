import './App.css'
import MainPage from './components/page'

function App() {
  return (
    <>
      {/* @ts-expect-error Server Component */}
      <MainPage />
    </>
  )
}

export default App
