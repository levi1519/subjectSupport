from django import forms


class SimulatorAttemptForm(forms.Form):

    def __init__(self, questions, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for q in questions:
            self.fields[f'question_{q.id}'] = forms.ChoiceField(
                choices=[('A','A'),('B','B'),('C','C'),('D','D')],
                required=False,
                widget=forms.RadioSelect(
                    attrs={'class': 'form-check-input'}
                ),
                label=q.statement,
            )

    def get_answers(self):
        answers = {}
        for key, value in self.cleaned_data.items():
            if key.startswith('question_'):
                qid = int(key.replace('question_', ''))
                answers[qid] = value if value else None
        return answers
