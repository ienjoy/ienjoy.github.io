def process_contact_info(name, email, message):
  """
  This function processes the submitted contact information.

  Args:
      name: User's name from the form.
      email: User's email from the form.
      message: User's message from the form.
  """
  print(f"Name: {name}")
  print(f"Email: {email}")
  print(f"Message: {message}")
  # You can add logic here to store the information in a database, send an email notification, etc.

if __name__ == "__main__":
  # Get form data from the request object (assuming a web server framework)
  name = request.form["name"]
  email = request.form["email"]
  message = request.form["message"]

  # Process the information
  process_contact_info(name, email, message)
