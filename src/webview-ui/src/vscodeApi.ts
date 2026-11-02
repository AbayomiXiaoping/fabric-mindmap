declare function acquireVsCodeApi(): {
  postMessage(message: unknown): void;
  getState(): unknown;
  setState(state: unknown): void;
};

class VSCodeAPI {
  private vsCode: ReturnType<typeof acquireVsCodeApi> | null = null;

  constructor() {
    if (typeof acquireVsCodeApi !== 'undefined') {
      this.vsCode = acquireVsCodeApi();
    }
  }

  postMessage(message: unknown): void {
    if (this.vsCode) {
      this.vsCode.postMessage(message);
    } else {
      console.log('[Webview mock postMessage]', message);
    }
  }

  getState<T>(): T | undefined {
    return this.vsCode?.getState() as T | undefined;
  }

  setState<T>(state: T): void {
    this.vsCode?.setState(state);
  }
}

export const vscode = new VSCodeAPI();

