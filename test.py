
import shutil
import os

src_path = r"E://recovered_all//MainFolder//Фото самсунг"
dest = r"E://recovered_all//Sorted"
fname = "20170529_215517.mp4"
src_path = os.path.join(src_path, fname)
dest = os.path.join(dest, fname)
print(os.path.exists(src_path))
print(os.path.exists(dest))
shutil.move(src_path, dest)