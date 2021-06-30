class CustomError(Exception):
  # Base classs for other exceptions
  pass

class CompilerError(CustomError):
  # TODO Make more specefic
  # Raised when there is an error setting up experiments
  def __init__(self, message):
    self.message = message