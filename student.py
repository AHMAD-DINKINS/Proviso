
class Student:

  def __init__(self, email):
    self.email = email
    self.submissions = []

  def get_email(self):
    return self.email

  def get_submissions(self):
    return self.submissions

  def add_submission(self, sub):
    self.submissions.append(sub)
    

  