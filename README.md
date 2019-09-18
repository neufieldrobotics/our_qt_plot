# our_qt_plot
A plotting tool with GUI for rosbags converted into pandas dataframes

## Input data structure
![Alt text](https://g.gravizo.com/source/svg/input_data_structure_dot?https%3A%2F%2Fraw.githubusercontent.com%2Fneufieldrobotics%2Four_qt_plot%2Fmaster%2FREADME.md)
<details> 
<summary></summary>
input_data_structure_dot
 digraph G {
    size ="4,4";
    main [shape=box];
    main -> parse [weight=8];
    parse -> execute;
    main -> init [style=dotted];
    main -> cleanup;
    execute -> { make_string; printf};
    init -> make_string;
    edge [color=red];
    main -> printf [style=bold,label="100 times"];
    make_string [label="make a string"];
    node [shape=box,style=filled,color=".7 .3 1.0"];
    execute -> compare;
  }
input_data_structure_dot
</details>
