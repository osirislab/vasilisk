let f = (o) => {
  var obj = [1,2,3];
  var x = Math.ceil(Math.random());
  return obj[o+x];
}

for (let i = 0; i < 0x10000; ++i) {
 f(i);
}

console.log("Hello World")
