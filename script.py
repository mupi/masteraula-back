from mupi_question_database.questions.models import Question, Answer, Subject
import json

counter = 1
with open('questions.json') as data_file:
    data = json.load(data_file)
    for question_data in data["questions"]:
        counter = counter + 1

        # verify if the question has one and just one right answer
        right_answer = False
        message = ''
        if "answers" in question_data and len(question_data["answers"]) > 0:
            for answer_data in question_data["answers"]:
                if answer_data['is_correct'] and not right_answer:
                    right_answer = True
                elif answer_data['is_correct'] and right_answer:
                    message = ('Question ' + str(counter) + ' has two right answer')
            if not right_answer:
                print('Question ' + str(counter) + ' dont have right answer')
                continue
            if message != '':
                print(message)
                continue

        question = Question.objects.create(question_statement=question_data["question_statement"],
                                            level=question_data["level"],
                                            resolution=question_data["resolution"],
                                            year=question_data["year"],
                                            source=question_data["source"],
                                            education_level=question_data["education_level"],
                                            author_id=1)

        if "answers" in question_data and len(question_data["answers"]) > 0:
            for answer_data in question_data["answers"]:
                answer = Answer.objects.create(answer_text=answer_data["answer_text"],
                                                    is_correct=answer_data["is_correct"],
                                                    question_id=question.id)

        for subject_id in question_data["subjects"]:
            subject = Subject.objects.get(pk=subject_id)
            question.subjects.add(subject)

        for tag in question_data["tags"]:
            question.tags.add(tag)
            question.save()
print('Done data')
