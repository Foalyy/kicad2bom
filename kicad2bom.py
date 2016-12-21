#!/usr/bin/env python3

import argparse, sys, os, re
from urllib.parse import urlparse
from operator import itemgetter

# Command-line argument parser
parser = argparse.ArgumentParser(
    description="Reads one or more Kicad schematics and extracts a Bill Of Materials",
    epilog="All filters accept comma-separated lists, for example : \"-V 100nF,1µF,10µF\"")
parser.add_argument("schematics", metavar="schematic", nargs="+", help="list of Kicad schematics (.sch) or project folders")
parser.add_argument("-u", "--unspecified", action="store_true", dest="unspecified", help="Show only components missing a supplier URL")
parser.add_argument("-a", "--all", action="store_true", dest="all",
    help="Show all components, including those with a placeholder (such as \"-\") instead of the supplier URL")
parser.add_argument("--cart", action="store_true", dest="cart", 
    help="Create separate CSV files for each supplier, group by supplier reference, and compute quantities for quick order. "
    "-o and -n are ignored, -s defaults to \"ref,value\" and -f accepts the \"qty\" field and its default value is \"supplier_ref,qty,url,name,value\".")
parser.add_argument("-m", "--multipliers", dest="multipliers", default="1",
    help="Quantity multipliers, to be used in conjonction with --cart. Accepts either one global multiplier, or a comma-separated list of multipliers for each schematic.")
group = parser.add_argument_group("Output format")
group.add_argument("-o", "--output", dest="output", help="CSV output file name. If missing, result is printed to stdout.")
group.add_argument("-n", "--number", action="store_true", dest="printnumber", help="Print the number of components selected")
group.add_argument("-H", "--no-header", action="store_true", dest="noheader", help="Do not output header")
group.add_argument("-f", "--fields", dest="fields",
    help="Comma-separated list of fields to output among 'schematic', "
    "'name', 'ref, 'value', 'footprint', 'url', 'supplier' and 'supplier_ref'. Default : \"schematic,ref,value,supplier,supplier_ref,url\" "
    "(\"schematic\" field is ommited if only one schematic is read)")
group.add_argument("-s", "--sort", dest="sort",
    help="Comma-separated list of fields used to sort the result. Default : \"schematic,ref\"")
group.add_argument("-d", "--delimiter", dest="delimiter", default="c", choices=["c", "s", "t"], 
    help="CSV delimiter : c=, s=; t=tabulation. Default : c.")
group.add_argument("-t", "--no-text-delimiter", action="store_true", dest="notextdelimiter",
    help="Do not delimit CSV text fields with \"quotes\"")
group = parser.add_argument_group("Filters")
group.add_argument("-N", "--name", dest="name", help="Filter by component name")
group.add_argument("-R", "--ref", dest="ref", help="Filter by reference")
group.add_argument("-V", "--value", dest="value", help="Filter by value")
group.add_argument("-F", "--footprint", dest="footprint", help="Filter by footprint")
group.add_argument("-S", "--supplier", dest="supplier", help="Filter by supplier")
group.add_argument("-Z", "--supplier_ref", dest="supplier_ref", help="Filter by supplier reference")

args = parser.parse_args()

# List of components extracted from Kicad
components = []

fields = ["schematic", "name", "ref", "value", "footprint", "url", "supplier", "supplier_ref"]

csvDelimiters = {"c":",", "s":";", "t":"\t"}

# Splits a string according to spaces just like string.split() but keeps double-quote-delimited text together
# For example : 'F 1 "100nF 50V" H 5150 1125' -> ['F', '1', '100nF 50V', 'H', '5150', '1125']
def split(string):
    output = []
    temp = ""
    inText = False
    multispace = False
    for l in string:
        if l == " " and not inText:
            if not multispace:
                output.append(temp)
                temp = ""
            multispace = True
        elif l == "\"":
            inText = not inText
            multispace = False
        else:
            temp += l
            multispace = False
    if temp != "":
        output.append(temp)
    return output


if __name__ == "__main__":

    # Check the number of multipliers
    args.multipliers = [int(x) for x in args.multipliers.split(",")]
    if not len(args.multipliers) == 1 and not len(args.multipliers) == len(args.schematics):
        print("Error : you can either specify one multiplier per schematic or one globally")
        sys.exit(0)

    # Find the list of schematics to parse
    schematics = []
    multipliers = []
    for i in range(len(args.schematics)):
        schematic = args.schematics[i]
        multiplier = args.multipliers[0]
        if len(args.multipliers) > 1:
            multiplier = args.multipliers[i]

        if os.path.isfile(schematic):
            schematics.append(schematic)
            multipliers.append(multiplier)
        elif os.path.isfile(schematic + ".sch"):
            schematics.append(schematic + ".sch")
            multipliers.append(multiplier)
        elif os.path.isdir(schematic):
            if not schematic.endswith("/"):
                schematic += "/"
            for e in os.listdir(schematic):
                if e.endswith(".sch") and os.path.isfile(schematic + e):
                    schematics.append(schematic + e)
                    multipliers.append(multiplier)

    # Extracts a global list of components for all the schematics
    for i in range(len(schematics)):
        schematic = schematics[i]

        # Open file
        try:
            file = open(schematic)
        except FileNotFoundError:
            print("Error : no such file: "  + schematic)
            sys.exit(0)

        # Get file name
        filename = os.path.splitext(os.path.basename(schematic))[0]

        # Read file and extract components
        inCompDef = False
        comp = None
        for line in file:
            line = line.strip()
            if line == "$Comp":
                comp = {}
                for field in fields:
                    comp[field] = ""
                comp["schematic"] = filename
                comp["multiplier"] = multipliers[i]
                inCompDef = True
            elif line == "$EndComp":
                components.append(comp.copy())
                inCompDef = False
            elif inCompDef:
                line = split(line)
                if line[0] == "L":
                    comp["name"] = line[1]
                elif line[0] == "F":
                    if line[1] == "0":
                        comp["ref"] = line[2]
                    elif line[1] == "1":
                        comp["value"] = line[2]
                    elif line[1] == "2":
                        comp["footprint"] = line[2]
                    elif line[1] == "3":
                        comp["url"] = line[2]
        file.close()

    # Compute additional fields
    for comp in components:
        if comp["url"].startswith("http"):
            url = urlparse(comp["url"])
            if "farnell" in url.netloc:
                comp["supplier"] = "farnell"
                comp["supplier_ref"] = url.path.split("/")[-1]
            elif "mouser" in url.netloc:
                comp["supplier"] = "mouser"
                if url.path.startswith("/search/ProductDetail.aspx"):
                    comp["supplier_ref"] = url.query.split("virtualkey")[-1]
                elif url.path.startswith("/ProductDetail/"):
                    comp["supplier_ref"] = url.path.split("/")[-2]
            elif "digikey" in url.netloc:
                comp["supplier"] = "digikey"
                comp["supplier_ref"] = url.path.split("/")[-2]

    # Apply filters
    components2 = components
    components = []
    for comp in components2:
        keep = True
        if comp["ref"].startswith("#"):
            keep = False
        if args.unspecified and comp["url"] != "":
            keep = False
        if not args.all and len(comp["url"]) == 1:
            keep = False
        for f in ["name", "ref", "value", "footprint", "supplier", "supplier_ref"]:
            if getattr(args, f) != None:
                if comp[f].lower() not in getattr(args, f).lower().split(","):
                    keep = False
        if keep:
            components.append(comp)

    # Sort (use natural sort for some fields)
    sortOrder = ""
    if args.sort == None:
        if args.cart:
            sortOrder = "ref,value"
        else:
            sortOrder = "schematic,ref"
    else:
        sortOrder = args.sort
    sortOrder = sortOrder.split(",")
    for field in sortOrder:
        if field not in fields:
            print("Error : unknown field \"" + field + "\"")
            sys.exit(0)
    convert = lambda x: int(x) if x.isdigit() else x.lower()
    alphanumKey = lambda x: [convert(x) for x in re.split('([0-9]+)', x)]
    sortOrder.reverse()
    for field in sortOrder:
        if field in ["ref", "value", "supplier_ref"]:
            components.sort(key=lambda comp: alphanumKey(comp[field]))
        else:
            components.sort(key=lambda comp: comp[field])

    # Select fields to export
    f = ""
    if args.fields == None:
        if args.cart:
            f = "supplier_ref,qty,url,name,value"
        else:
            if len(args.schematics) >= 2:
                f = "schematic,"
            f += "ref,value,supplier,supplier_ref,url"
    else:
        f = args.fields
    outputFields = f.split(",")
    if args.cart:
        fields.append("qty")
    for field in outputFields:
        if field not in fields:
            print("Error : unknown field \"" + field + "\"")
            sys.exit(0)

    # CSV parameters
    csvDelimiter = csvDelimiters[args.delimiter]
    textDelimiter = "\""
    if args.notextdelimiter:
        textDelimiter = ""

    # Output
    if args.output == None and not args.cart:
        # Prints the list on the standard output

        # Computes the size of each field
        fieldsSize = {}
        for field in outputFields:
            m = len(field)
            for comp in components:
                n = len(comp[field])
                if n > m:
                    m = n
            fieldsSize[field] = m + 2

        # Print header
        if not args.noheader:
            for field in outputFields:
                s = field.upper()
                print(s, end="")
                print(" " * (fieldsSize[field] - len(s)), end="")
            print()

        # Prints components list
        for comp in components:
            for field in outputFields:
                s = comp[field]
                print(s, end="")
                print(" " * (fieldsSize[field] - len(s)), end="")
            print()

        if args.printnumber:
            print("Total : " + str(len(components)) + " components")

    elif args.cart:
        # Compute quantities for each component of each supplier
        suppliers = {}
        for comp in components:
            supplier = comp["supplier"]
            if supplier not in suppliers:
                suppliers[supplier] = []
            ref = comp["supplier_ref"]
            listRefs = [c["supplier_ref"] for c in suppliers[supplier]]
            if ref not in listRefs:
                comp2 = comp.copy()
                comp2["qty"] = comp["multiplier"]
                del comp2["multiplier"]
                suppliers[supplier].append(comp2)
            else:
                suppliers[supplier][listRefs.index(ref)]["qty"] += comp["multiplier"]

        for supplier in suppliers:
            # Open output file
            filename = supplier + ".csv"
            file = open(filename, "w")

            # Write header
            if not args.noheader:
                for field in outputFields:
                    file.write(textDelimiter + field.upper() + textDelimiter + csvDelimiter)
                file.write("\n")

            # Write components list
            for comp in suppliers[supplier]:
                for field in outputFields:
                    if field == "qty":
                        file.write(str(comp[field]) + csvDelimiter)
                    else:
                        file.write(textDelimiter + str(comp[field]) + textDelimiter + csvDelimiter)
                file.write("\n")
            file.close()


    else:
        # Open output file
        filename = args.output.strip()
        if not filename.endswith(".csv"):
            filename += ".csv"
        file = open(filename, "w")

        # Write header
        if not args.noheader:
            for field in outputFields:
                file.write(textDelimiter + field.upper() + textDelimiter + csvDelimiter)
            file.write("\n")

        # Write components list
        for comp in components:
            for field in outputFields:
                file.write(textDelimiter + comp[field] + textDelimiter + csvDelimiter)
            file.write("\n")
        file.close()

