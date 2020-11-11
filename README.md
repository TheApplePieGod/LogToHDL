## LogToHDL

A python script that will take a logisim .circ file and convert it into nand2tetris hdl code to be placed in the parts section.

Current limitations:
- All gates must be facing east (inputs and outputs can be any direction)
- Limited to one output node (for now)
- All input and output nodes must be labeled or you will get randomized i/o array accessors
- Greater than two inputs per node are supported, but as far as I know, n2t hdl doesn't support, for example, `And(a=a,b=b,c=c,out=out)` with more than 2 inputs

Supported nodes: input, output, and, or, not, nand, xor, nor, xnor

Example:
![Example Image](https://github.com/TheApplePieGod/LogToHDL/blob/master/images/example.png?raw=true)

Produces:
`
HDL Output:

And(c=B,a=D,b=C,out=output3);
Nand(b=B,a=D,c=A,out=output5);
Not(a=D,out=output6);
Or(b=output5,a=output6,out=output1);
Not(a=B,out=output7);
And(b=output7,a=C,out=output0);
And(b=output1,a=output0,out=output2);
Or(a=output3,b=output2,out=Out);
`