from rolepermissions.roles import AbstractUserRole

class Teacher(AbstractUserRole):
    available_permissions = {
        'create_question_list': True,
    }

class Student(AbstractUserRole):
    available_permissions = {
        # 'edit_patient_file': True,
    }
