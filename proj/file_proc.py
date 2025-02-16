import os
import subprocess

class TestCase:
    def __init__(self, input_data, expected_output):
        self.input_data = input_data
        self.expected_output = expected_output

class TestCaseParser:
    @staticmethod
    def parse_file(file_path):
        with open(file_path, 'r', encoding="utf-8") as f:
            content = f.read().split()
        
        test_cases = []
        current_input = ""
        
        for i in range(len(content)):
            if content[i][-1] == "Q":
                current_input = ""
            elif content[i][-1] == "A":
                test_cases.append(TestCase(current_input, content[i + 1]))
            else:
                current_input += content[i] + "\n"
                
        return test_cases

class CodeExecutor:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def execute(self, input_data):
        process = subprocess.Popen(
            ['python', self.file_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=input_data.encode())
        return stdout.decode(), stderr.decode()

class TestRunner:
    def __init__(self, executor):
        self.executor = executor
        
    def run_test(self, test_case):
        output, error = self.executor.execute(test_case.input_data)
        if error:
            return False, error
        return output[:-2] == test_case.expected_output, output

class FileProcessor:
    def __init__(self, file_path, num_task):
        self.executor = CodeExecutor(file_path)
        self.test_runner = TestRunner(self.executor)
        self.num_task = num_task
        
    def process_file(self):
        current_file = os.path.realpath(__file__)
        testcase_path = os.path.dirname(current_file) + f'\\TestCases\\test{self.num_task}'
        
        test_cases = TestCaseParser.parse_file(testcase_path)
        
        for i, test_case in enumerate(test_cases, 1):
            success, result = self.test_runner.run_test(test_case)
            if not success:
                return f"После прохождения тест-кейса №{i}, была обнаружена ошибка"
                
        return "Программа работает верно"