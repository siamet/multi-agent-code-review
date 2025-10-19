/**
 * Sample JavaScript file for testing parser
 */

function helloWorld() {
  console.log("Hello, World!");
}

class Calculator {
  constructor() {
    this.result = 0;
  }

  add(a, b) {
    this.result = a + b;
    return this.result;
  }

  subtract(a, b) {
    this.result = a - b;
    return this.result;
  }
}

const greet = (name) => {
  return `Hello, ${name}!`;
};

export { Calculator, greet, helloWorld };
