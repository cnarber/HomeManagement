import random

def generateTimesTable():
    questions = []
    for i in range(1,13):
        for j in range(1,13):
            questions.append({
                "question": "What is {} x {}?".format(i,j),
                "type": "field_input",
                "answer":i*j
            })
    random.shuffle(questions)
    for i,q in enumerate(questions):
        q['id'] = "q"+str(i+1)
    return questions