import os
import re
import shutil
import filecmp


class Syncronizer(object):
    def __init__(self):
        self._include = list()
        self._exclude = list()

    def compare_directories(self, src_dir, dst_dir, exclude_patterns=None):
        if not (os.path.isdir(src_dir) and os.path.isdir(dst_dir)):
            raise Exception('src and dest must be a valid directories.')

        src_set = set()
        dst_set = set()
        num_dirs = 0
        num_dirs += 1

        exclude_patterns = exclude_patterns or list()

        for cwd, dirs, files in os.walk(src_dir):
            num_dirs += len(dirs)
            all_items = dirs + files
            for each_item in all_items:
                path = os.path.relpath(os.path.join(cwd, each_item), src_dir)
                re_path = path.replace('\\', '/')

                for pattern in exclude_patterns:
                    if not re.match(pattern, re_path):
                        continue
                    break

                src_set.add(path)

        for cwd, dirs, files in os.walk(dst_dir):
            all_items = dirs + files
            for each_item in all_items:
                path = os.path.relpath(os.path.join(cwd, each_item), dst_dir)
                re_path = path.replace('\\', '/')
                for pattern in self._exclude:
                    if re.match(pattern, re_path):
                        break

                dst_set.add(path)

        common_items = src_set.intersection(dst_set)
        source_items = list(src_set - common_items)
        dest_items = list(dst_set - common_items)

        return source_items, dest_items, common_items

    @staticmethod
    def delete_file(fp):
        if os.path.isfile(fp):
            os.remove(fp)

        elif os.path.isdir(fp):
            try:
                shutil.rmtree(fp, True)
            except shutil.Error as e:
                pass

    @staticmethod
    def compare_file_timestamp(fp1, fp2, check_contents=False):
        if check_contents:
            return filecmp.cmp(fp1, fp2, shallow=False)

        fp1_stat = os.stat(fp1)
        fp2_stat = os.stat(fp2)
        return int(fp1_stat.st_mtime) == int(fp2_stat.st_mtime)

    def _copy_file(self, src_file, dst_file):
        print('Copying file: {} to {}'.format(src_file, dst_file))
        dst_dir_name = os.path.dirname(dst_file)
        self.create_directory(dst_dir_name)
        file_name = os.path.basename(src_file)
        if os.path.islink(src_file):
            return os.symlink(os.readlink(src_file), os.path.join(dst_file, file_name))
        else:
            copied_file = shutil.copy2(src_file, dst_file)

        shutil.copystat(src_file, dst_file)
        return copied_file

    @staticmethod
    def create_directory(directory_path):
        if os.path.exists(directory_path):
            return directory_path

        os.makedirs(directory_path)
        return directory_path

    def sync(self, src_dir, dst_dir, delete=True, copier=None):
        created = list()
        modified = list()
        deleted = list()

        src_new_files, dest_new_files, common_files = self.compare_directories(src_dir=src_dir, dst_dir=dst_dir)
        if not copier:
            copier = self._copy_file

        for file_name in common_files:
            src_fp = os.path.join(src_dir, file_name)
            dst_fp = os.path.join(dst_dir, file_name)
            if os.path.isdir(src_fp):
                self.create_directory(dst_fp)
                continue

            # has_changes = filecmp.cmp(src_fp, dst_fp, not check_contents)
            has_changes = not self.compare_file_timestamp(src_fp, dst_fp, check_contents=True)
            if not has_changes:
                continue

            copied_file = copier(src_fp, dst_fp)
            modified.append(copied_file)

        for file_name in src_new_files:
            src_fp = os.path.join(src_dir, file_name)
            dst_fp = os.path.join(dst_dir, file_name)

            if os.path.isfile(src_fp):
                copied_file = copier(src_fp, dst_fp)
                created.append(copied_file)

            elif os.path.isdir(src_fp):
                created_dir = self.create_directory(dst_fp)
                created.append(created_dir)

        if not delete:
            return

        for file_name in dest_new_files:
            dst_file = os.path.join(src_dir, file_name)
            self.delete_file(dst_file)
            deleted.append(dst_dir)


if __name__ == '__main__':
    s = Syncronizer()
    t_src = r'D:\test\src'
    t_dst = r'D:\test\dst'
    print(s.sync(t_src, t_dst))
