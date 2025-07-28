import os
import shutil
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import pillow_heif
import hashlib

pillow_heif.register_heif_opener()

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.3gp', 'mts')



def count_files_in_directory(directory):
    total = 0
    for _, _, files in os.walk(directory):
        total += len(files)
    return total


def calculate_file_hash(filepath, chunk_size=8192):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
    except Exception as e:
        print(f"Error calculating hash for {filepath}: {e}")
        return None
    return sha256.hexdigest()

def is_duplicate(file1, file2):
    """
    Check if two files are duplicates based on size and SHA-256 hash.
    """
    try:
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        if not hash1 or not hash2:
            return False

        return hash1 == hash2
    except Exception as e:
        print(f"Error checking duplicate between {file1} and {file2}: {e}")
        return False

def get_image_year(filepath):
    try:
        image = Image.open(filepath)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id)
                if tag == 'DateTimeOriginal':
                    return datetime.strptime(value, '%Y:%m:%d %H:%M:%S').year
    except Exception:
        pass
    return fallback_year(filepath)

def get_video_year(filepath):
    parser = createParser(filepath)
    if not parser:
        return fallback_year(filepath)
    try:
        metadata = extractMetadata(parser)
        if metadata and metadata.has("creation_date"):
            return metadata.get("creation_date").year
    except Exception:
        pass
    finally:
        # This ensures the file is closed even if an error occurs
        parser.close()
    return fallback_year(filepath)

def fallback_year(filepath):
    mod_time = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mod_time).year

def move_file_safe(src_path, dest_path, duplicates_folder, count):
    try:
        if os.path.exists(dest_path):
            if is_duplicate(src_path, dest_path):
                # Full duplicate: move to duplicates folder with original name (or numbered if needed)
                os.makedirs(duplicates_folder, exist_ok=True)
                duplicate_dest = os.path.join(duplicates_folder, os.path.basename(src_path))
                count = 1
                name, ext = os.path.splitext(os.path.basename(src_path))
                while os.path.exists(duplicate_dest):
                    duplicate_dest = os.path.join(duplicates_folder, f"{name}_{count}{ext}")
                    count += 1
                shutil.move(src_path, duplicate_dest)
                print(f"Full Duplicate detected and moved: {src_path} -> {duplicate_dest}")
            else:
                # File with same name but different content: rename and save in destination folder
                dest_folder = os.path.dirname(dest_path)
                name, ext = os.path.splitext(os.path.basename(dest_path))
                count = 1
                new_dest_path = dest_path
                while os.path.exists(new_dest_path):
                    new_dest_path = os.path.join(dest_folder, f"{name}_{count}{ext}")
                    count += 1
                shutil.move(src_path, new_dest_path)
                print(f"Name conflict resolved and moved: {src_path} -> {new_dest_path}")
        else:
            shutil.move(src_path, dest_path)
            print(f"{count} Moved: {src_path} -> {dest_path}")
    except Exception as e:
        print(f"Error moving file {src_path}: {e}")

def copy_media_sorted_by_year(source_folder, photo_dest_folder, video_dest_folder, duplicate_root):
    # File counts before moving
    source_file_count = count_files_in_directory(source_folder)
    pre_photo_count = count_files_in_directory(photo_dest_folder)
    pre_video_count = count_files_in_directory(video_dest_folder)
    pre_duplicate_count = count_files_in_directory(duplicate_root)
    pre_sorted_count = pre_duplicate_count+pre_video_count+pre_photo_count

    print(f"\nInitial Counts:")
    print(f"  Source files: {source_file_count}")
    print(f"  Photo destination files: {pre_photo_count}")
    print(f"  Video destination files: {pre_video_count}\n")
    print(f"  Duplicate destination files: {pre_duplicate_count}\n")

    if not os.path.isdir(source_folder):
        print(f"Source folder '{source_folder}' does not exist.")
        return
    count = 0
    for root, _, files in os.walk(source_folder):
        for file in files:
            file_lower = file.lower()
            src_path = os.path.join(root, file)

            if file_lower.endswith(IMAGE_EXTENSIONS):
                year = get_image_year(src_path)
                base_dest = photo_dest_folder
                duplicate_dest = os.path.join(duplicate_root, "Photo", str(year))
            elif file_lower.endswith(VIDEO_EXTENSIONS):
                year = get_video_year(src_path)
                base_dest = video_dest_folder
                duplicate_dest = os.path.join(duplicate_root, "Video", str(year))
            else:
                continue

            year_folder = os.path.join(base_dest, str(year))
            os.makedirs(year_folder, exist_ok=True)

            dest_path = os.path.join(year_folder, file)
            count +=1
            move_file_safe(src_path, dest_path, duplicate_dest, count)


    post_photo_count = count_files_in_directory(photo_dest_folder)
    post_video_count = count_files_in_directory(video_dest_folder)
    post_duplicate_count = count_files_in_directory(duplicate_root)
    post_total_sorted_files = post_photo_count + post_video_count + post_duplicate_count
    moved_files = post_total_sorted_files - (pre_photo_count + pre_video_count + pre_duplicate_count)
    check = source_file_count - moved_files

    print(f"\nPost Counts:")
    print(f"  Files moved: {moved_files}")
    print(f"  Sorted total before: {pre_sorted_count}")
    print(f"  Sorted total post: {post_total_sorted_files}")
    print(f"  Duplicate count: {post_duplicate_count - pre_duplicate_count}")
    print(f"  Check sum: {check}\n")


# Example usage
source = r"E:/recovered_all/Мультимедиа Видео"
photo_destination = r"E:/recovered_all/Sorted/Photo"
video_destination = r"E:/recovered_all/Sorted/Video"
duplicates_root = r"E:/recovered_all/Sorted/Duplicates"

copy_media_sorted_by_year(source, photo_destination, video_destination, duplicates_root)
