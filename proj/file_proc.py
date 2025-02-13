import os
import subprocess

class FileProcessor:
    def __init__(self, file_path, num_task):
        self.file_path = file_path
        self.num_task = num_task

    def process_file(self):
        current_file = os.path.realpath(__file__)
        testcase_directory = os.path.dirname(current_file) + f'\\TestCases\\test{self.num_task}'
        with open(testcase_directory, 'r', encoding="utf-8") as f:
            file_content = f.read()
            file_mas = file_content.split()
        user_input = ""
        answer_correction = True
        content = ""
        # print(file_mas)
        for i in range(len(file_mas)):
            if file_mas[i][-1] == "Q":
                user_input = ""
            elif file_mas[i][-1] == "A":
                process = subprocess.Popen(['python', self.file_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(input=user_input.encode())
                output = stdout.decode()

                if output[:-2] != file_mas[i + 1]:
                    answer_correction = False
                    # print(output)
                if not output:
                    content = stderr.decode()
                    if not content:
                        content = file_mas[i + 1]
                    # print(stderr.decode())
            else:
                user_input += file_mas[i] + "\n"
        if answer_correction:
            content = "Программа работает верно"
        else:
            a = content
            content = f"После прохождения тест-кейса №{a}, была обнаружена ошибка"
        return content