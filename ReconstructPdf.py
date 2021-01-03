import io

class ReconstructPdf():
    def __init__(self):
        self.buffer = io.BytesIO()
        self.header_buffer = io.BytesIO()
        self.output = io.BytesIO()
        self.buffer_size = 0
        self.stream = False
        self.single_line_header = False
        self.first = True
        self.object_positions = {}
    
    def fix_xref_table(self, pdf_file):
        self.buffer = io.BytesIO()
        start_xref = 0
        pdf_file.seek(0, 0)
        while True:
            cursor = pdf_file.tell()
            current_line = pdf_file.readline()
            if not current_line:
                print(self.object_positions)
                asb = self.buffer
                return self.buffer.getvalue()
            if current_line.endswith(b' obj\n'):
                self.buffer.write(current_line)
                object_values = current_line.split(b' ')
                self.object_positions[int(object_values[0])] = cursor
            elif current_line == b'xref\n':
                self.buffer.write(current_line)
                start_xref = cursor
                line = pdf_file.readline()
                line = pdf_file.readline()
                self.buffer.write(b'0 {}\n'.format(len(self.object_positions)+1))
                self.buffer.write(b'0000000000 65535 f\n')
                for key in self.object_positions:
                    line = pdf_file.readline()
                    self.buffer.write(b'{:010d} 00000 n\n'.format(self.object_positions[key]))
            elif current_line == b'startxref\n':
                self.buffer.write(current_line)
                line = pdf_file.readline()
                self.buffer.write(b'{}\n'.format(start_xref))
            else:
                self.buffer.write(current_line)
        return 0


    def handle_stream(self, pdf_file, current_line):
        assert current_line == b'stream\r\n'
        self.buffer.write(current_line)
        while True:
            current_line = pdf_file.readline()
            self.buffer.write(current_line)
            if current_line == b'endstream\r\n':
                self.buffer_size -= 2
                self.stream = False
                break
            elif current_line.endswith(b'endstream\r\n'):
                c_line = current_line[:-11]
                self.buffer_size += len(c_line)
                self.stream = False
                break
            elif b'endstream\r\n' not in current_line:
                self.buffer_size += len(current_line)

    def append(self, pdf_file):
        self.output.write(self.header_buffer.getvalue())
        if "/Length" not in self.header_buffer.getvalue():
            self.output.write(b"/Length {}".format(buffer_size))
        self.output.write(b">>\r\n" if self.single_line_header else "\r\n>>\r\n")
        self.output.write(self.buffer.getvalue())
        return self.output

    def handle_header(self, pdf_file, current_line):
        header_buf = self.header_buffer.getvalue()
        if self.first:
            self.output.write(self.buffer.getvalue())
            self.first = False
        else:
            self.output.write(header_buf)
            if b'/Length' not in header_buf:
                self.output.write(b'/Length {}'.format(self.buffer_size))
            self.output.write(b">>\r\n" if self.single_line_header else "\r\n>>\r\n")
            self.output.write(self.buffer.getvalue())

        self.header_buffer = io.BytesIO()
        self.buffer = io.BytesIO()
        self.buffer_size = 0

        if current_line.endswith(b'>>\r\n'):
            self.single_line_header = True
            stripped_line = current_line[:-4]
            self.header_buffer.write(stripped_line)
            self.stream = True
        else:
            self.single_line_header = False
            self.header_buffer.write(current_line)
            while True:
                current_line = pdf_file.readline()
                if current_line == b'>>\r\n':
                    self.stream = True
                    break
                else:
                    self.header_buffer.write(current_line)

    def reconstruct(self, pdf_file):
        pdf_file.seek(0, 0)
        while True:
            current_line = pdf_file.readline()
            if not current_line:
                self.append(pdf_file)
                return self.output.getvalue()
            elif current_line.startswith(b'<< '):
                self.handle_header(pdf_file, current_line)
            elif self.stream:
                self.handle_stream(pdf_file, current_line)
            else:
                self.buffer.write(current_line)