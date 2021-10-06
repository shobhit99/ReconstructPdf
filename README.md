# ReconstructPdf

### Example Usage
```python
my_pdf_file = open("file.pdf", "r")
reconstructor = ReconstructPdf()
output_file = reconstructor.reconstruct(my_pdf_file)
open("output.pdf", "w").write(output_file.getvalue())
```
