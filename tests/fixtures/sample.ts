/**
 * Sample TypeScript file for testing parser
 */

interface Person {
  name: string;
  age: number;
}

function helloWorld(): void {
  console.log("Hello, World!");
}

class Calculator {
  private result: number;

  constructor() {
    this.result = 0;
  }

  add(a: number, b: number): number {
    this.result = a + b;
    return this.result;
  }

  subtract(a: number, b: number): number {
    this.result = a - b;
    return this.result;
  }
}

const greet = (name: string): string => {
  return `Hello, ${name}!`;
};

export { Calculator, greet, helloWorld, Person };
