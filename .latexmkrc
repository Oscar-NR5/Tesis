$pdflatex = 'pdflatex -interaction=nonstopmode -synctex=1 -file-line-error %O %S';
$pdf_mode = 1;
$out_dir = 'build';
$aux_dir = 'build';

# Solo este archivo es compilable; el resto son fragmentos que él \input.
# Sin esta línea, `latexmk` a secas intentaría compilar cada .tex suelto.
@default_files = ('main.tex');
