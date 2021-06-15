
class Student:

  def __init__(self, email, submssions):
    self.email = email
    self.submissions = submssions

  def get_email(self):
    return self.email

  def get_submissions_from_result(self, result):
    return self.submissions[result] if result in self.submissions else None

  