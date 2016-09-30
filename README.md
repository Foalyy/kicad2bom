# kicad2bom

## Presentation

This simple tool is able to 

- read a set of Kicad projects and/or schematics
- extract the list of components
- apply usual select/sort/filter operations
- output the result, either on the standard output or in a CSV file

Its goal is to make generating components shopping cart as quick and easy as possible (when used with suppliers' CSV importation tools).

## Install

Simply check that python3 is installed, then copy the script somewhere in your path. For example :

    sudo cp kicad2bom.py /usr/local/bin/kicad2bom

## How to use

For each component in your Kicad schematic, find on a supplier's website (such as Farnell, Mouser, Digikey, ...) and insert the reference in Kicad's Datasheet field. For example :

    http://fr.farnell.com/multicomp/mc0603b104k250ct/condensateur-mlcc-x7r-100nf-25v/dp/1759037

Supplier name and reference will be extracted from this URL (from known suppliers, feel free to add yours).

## Manpage

usage: kicad2bom.py [-h] [-u] [-a] [--cart] [-m MULTIPLIER] [-o OUTPUT] [-H]
                        [-f FIELDS] [-s SORT] [-d {c,s,t}] [-t] [-N NAME] [-R REF]
                        [-V VALUE] [-F FOOTPRINT] [-S SUPPLIER] [-Z SUPPLIER_REF]
                        schematic [schematic ...]

    Reads one or more Kicad schematics and extracts a Bill Of Materials

    positional arguments:
      schematic             list of Kicad schematics (.sch) or project folders

    optional arguments:
      -h, --help            show this help message and exit
      -u, --unspecified     Show only components missing a supplier URL
      -a, --all             Show all components, including those with a
                            placeholder (such as "-") instead of the supplier URL
      --cart                Create separate CSV files for each supplier, group by
                            supplier reference, and compute quantities for quick
                            order. -o is ignored, -s defaults to "ref,value" and
                            -f accepts the "qty" field and its default value is
                            "supplier_ref,qty,url,name,value".
      -m MULTIPLIERS, --multipliers MULTIPLIERS
                            Quantity multipliers, to be used in conjonction with
                            --cart. Accepts either one global multiplier, or a
                            comma-separated list of multipliers for each
                            schematic.

    Output format:
      -o OUTPUT, --output OUTPUT
                            CSV output file name. If missing, result is printed to
                            stdout.
      -H, --no-header       Do not output header
      -f FIELDS, --fields FIELDS
                            Comma-separated list of fields to output among
                            'schematic', 'name', 'ref, 'value', 'footprint',
                            'url', 'supplier' and 'supplier_ref'. Default :
                            "schematic,ref,value,supplier,supplier_ref,url"
                            ("schematic" field is ommited if only one schematic is
                            read)
      -s SORT, --sort SORT  Comma-separated list of fields used to sort the
                            result. Default : "schematic,ref"
      -d {c,s,t}, --delimiter {c,s,t}
                            CSV delimiter : c=, s=; t=tabulation. Default : c.
      -t, --no-text-delimiter
                            Do not delimit CSV text fields with "quotes"

    Filters:
      -N NAME, --name NAME  Filter by component name
      -R REF, --ref REF     Filter by reference
      -V VALUE, --value VALUE
                            Filter by value
      -F FOOTPRINT, --footprint FOOTPRINT
                            Filter by footprint
      -S SUPPLIER, --supplier SUPPLIER
                            Filter by supplier
      -Z SUPPLIER_REF, --supplier_ref SUPPLIER_REF
                            Filter by supplier reference

    All filters accept comma-separated lists, for example : "-V 100nF,1µF,10µF"

## Examples

Find every component missing a supplier URL :

    kicad2bom kicadproject/ -u

Get every capacitor and resistor :

    kicad2bom kicadproject/ -N C,R

Get the footprint of every component with 100nF or 1µF value, sorted by footprint and sub-sorted by value :

    kicad2bom kicadproject/ -f footprint,ref,value -V 100nf,1µF -s footprint,value

Create different CSV files for each supplier with quantities, ready to order to assemble 7 boards :

    kicad2bom kicadproject/ --cart -m 7

Compile multiple schematics to make 5 copies of this multi-board project with 2 spare power boards :

    kicad2bom board_power/ board_mcu/ board_antenna/ --cart -m 7,5,5

## Contributing

Feel free to add your own suppliers reference, fix bugs, improve features or correct my English mistakes, I'll gladly accept requests :)
