function f(x, y) {
  return x + y;
}

f("Hello ", "World");
%OptimizeFunctionOnNextCall(f);
f("Hello ", "World");
