# Reservation Rules

A reservation request needs five details: first name, last name, car number, start date and time, and end date and time. The assistant asks for them one at a time.

First and last names must contain letters only. Spaces, dots, hyphens and apostrophes are allowed.

The car number must follow the Indian registration format: two letters, one or two digits, one to three letters, then four digits. For example, TS09AB1234.

Dates and times are written as YYYY-MM-DD HH:MM on a 24 hour clock. For example, 2026-12-10 10:00.

The start must be in the future and the end must be after the start. A reservation can last at most 30 days.

Before sending anything, the assistant shows a summary and asks the customer to confirm. Nothing is sent without a clear yes.

After the customer confirms, the assistant gives a request id such as RES-3F9A1C. The request is not confirmed yet and waits for the administrator.

The customer can ask for the status of the request at any time. While the chat stays open, the assistant also announces the administrator's decision as soon as it arrives.

When the administrator approves a request, a space is reserved for the booked period and the booking is saved to the reservation register.

When the administrator refuses a request, the customer sees the reason if one was given. The customer can submit a new request for a different period.

If the last free space is taken before an approved booking is saved, the booking is not saved. The customer is told to contact the parking office.