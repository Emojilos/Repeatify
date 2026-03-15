import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[300px] flex-col items-center justify-center p-8 text-center">
          <div className="mb-4 text-4xl">&#9888;&#65039;</div>
          <h2 className="mb-2 text-lg font-semibold text-gray-900 dark:text-gray-100">
            Что-то пошло не так
          </h2>
          <p className="mb-4 max-w-md text-sm text-gray-500 dark:text-gray-400">
            Произошла непредвиденная ошибка. Попробуйте обновить страницу.
          </p>
          {this.state.error && (
            <p className="mb-4 max-w-md rounded bg-gray-100 px-3 py-2 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-400">
              {this.state.error.message}
            </p>
          )}
          <button
            onClick={this.handleReset}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
