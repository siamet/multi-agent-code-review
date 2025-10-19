/**
 * Sample Java file for testing parser
 */

package com.example.test;

import java.util.ArrayList;
import java.util.List;

public class Calculator {
    private int result;

    public Calculator() {
        this.result = 0;
    }

    public int add(int a, int b) {
        this.result = a + b;
        return this.result;
    }

    public int subtract(int a, int b) {
        this.result = a - b;
        return this.result;
    }

    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println("5 + 3 = " + calc.add(5, 3));
        System.out.println("10 - 4 = " + calc.subtract(10, 4));
    }
}

class Helper {
    public static void helloWorld() {
        System.out.println("Hello, World!");
    }
}
