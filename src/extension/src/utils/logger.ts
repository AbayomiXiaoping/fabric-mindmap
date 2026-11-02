import * as vscode from 'vscode';

const SENSITIVE_KEYWORDS = ['token', 'secret', 'key', 'password', 'bearer', 'authorization'];

export class Logger {
  private outputChannel: vscode.OutputChannel;
  private prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
    this.outputChannel = vscode.window.createOutputChannel('Lakehouse Intelligence');
  }

  private redact(message: string): string {
    let clean = message;
    for (const kw of SENSITIVE_KEYWORDS) {
      const regex = new RegExp(`(${kw}["'\\s:=]+)([^"\\s,;]+)`, 'gi');
      clean = clean.replace(regex, '$1***REDACTED***');
    }
    return clean;
  }

  private log(level: string, message: string): void {
    const timestamp = new Date().toISOString();
    const cleanMsg = this.redact(message);
    this.outputChannel.appendLine(`[${timestamp}] [${level}] [${this.prefix}] ${cleanMsg}`);
  }

  info(message: string): void {
    this.log('INFO', message);
  }

  warn(message: string): void {
    this.log('WARN', message);
  }

  error(message: string, error?: unknown): void {
    const errorDetails = error instanceof Error ? `\n${error.stack || error.message}` : '';
    this.log('ERROR', `${message}${errorDetails}`);
  }

  debug(message: string): void {
    this.log('DEBUG', message);
  }

  show(): void {
    this.outputChannel.show(true);
  }
}

