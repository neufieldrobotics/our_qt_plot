# our_qt_plot
A plotting tool with GUI for rosbags converted into pandas dataframes

## Input data structure
![Alt text](https://g.gravizo.com/source/svg/input_ds?https%3A%2F%2Fraw.githubusercontent.com%2Fneufieldrobotics%2Four_qt_plot%2Fmaster%2FREADME.md)
<details> 
<summary></summary>
input_ds
digraph G {
"data_file.pkl" -> "full_data_dict";
"full_data_dict" -> "namespace1 dict" [color="orange"];
"full_data_dict" -> "namespace2 dict" [color="orange"];
n1t1 [label="topic1 pandas df"];
n1t2 [label="topic2 pandas df"];
n2t1 [label="topic1 pandas df"];
n2t2 [label="topic2 pandas df"];
"namespace1 dict" -> n1t1 [color="green"];
"namespace1 dict" -> n1t2 [color="green"];
"namespace2 dict" -> n2t1 [color="green"];
"namespace2 dict" -> n2t2 [color="green"];
n1t1t [label="Time\n(index)"];
n1t1f1 [label="Field1\ncolumn"];
n1t1f2 [label="Field2\ncolumn"];
n1t2t [label="Time\n(index)"];
n1t2f1 [label="Field1\ncolumn"];
n1t2f2 [label="Field2\ncolumn"];
n2t1t [label="Time\n(index)"];
n2t1f1 [label="Field1\ncolumn"];
n2t1f2 [label="Field2\ncolumn"];
n2t2t [label="Time\n(index)"];
n2t2f1 [label="Field1\ncolumn"];
n2t2f2 [label="Field2\ncolumn"];
n1t1 -> n1t1t [color="blue"];
n1t1 -> n1t1f1 [color="blue"];
n1t1 -> n1t1f2 [color="blue"];
n1t2 -> n1t2t [color="blue"];
n1t2 -> n1t2f1 [color="blue"];
n1t2 -> n1t2f2 [color="blue"];
n2t1 -> n2t1t [color="blue"];
n2t1 -> n2t1f1 [color="blue"];
n2t1 -> n2t1f2 [color="blue"];
n2t2 -> n2t2t [color="blue"];
n2t2 -> n2t2f1 [color="blue"];
n2t2 -> n2t2f2 [color="blue"];
}
input_ds
</details>
