#!/usr/bin/env python3
jabooby = 0
max_jab = 979879
with open("es6.ebnf.1", "r") as gramm:
    for line in gramm:
        line = [x.strip(" ") for x in line.split("::=")]
        line = " := | " .join(line)
        line = line.strip().replace(" | ", "\n\t")
        print(line.split(":=")[0] + " := ", end = "")
        for i in range(1, len(line.split(":="))):
            new = line.split(":=")[i]
            if new[2] == "\"":
                print(new)
            else:
                new2 = new[2:]
                for i in new2.split("\n\t"):
                    print("\n\t" + "+" + i + "+", end = "")
                #print("\n\t" + "+" + new[2:].s + "+")
            print()
        print()
        jabooby += 1
        if jabooby == max_jab:
            break
