
# ModernConnect

ModernConnect is a Professional Social Media built exclusively for students and alumnus of Modern College of Engineering, Pune.

This project will allow students to seek help from their Peers and the Alumni, also share their skills, Post about events, etc. 
The motto of this project is to increase the overall involvement of the Alumnus with the college and mentor the students for better future opportunities. The Project is currently in the development phase. 
The Technology Stack for this Project are Python/Django, React, MongoDB

The Research Paper for this project is published in UIJRT Volume 3, Issue 6. [Read the research paper here.](https://uijrt.com/paper/exclusive-platform-for-students-alumni-mcoe-pune-connect)

This GitHub repository includes code for ModernConnect's API.


# API Reference

## General User-related URLs.

#### Register User 

```http
  POST /api/v1/user/signup/
```
Users can be of two types, either a Student or an Alumni.     \
 **All parameters are required.**
| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `user_name` | `string` | example: "sarvesh_joshi" |
| `password` | `string` | example: "FakePassword" |
| `email_address` | `string` |For Students - @moderncoe.edu.in email address is required. |
| `full_name` | `string` | example: "Sarvesh Joshi" |
| `account_type` | `string` | Student/Alumni |
| `gender` | `string` | M/F/O |
| `contact_number` | `string` | example: "1234567890" |
| `about_yourself` | `string` | example: "Backend Developer" |

**Steps to follow after successful creation of account :**   
    1. On successful creation of an account - An email with verification code is sent. The User need to verify his/her/their Email address to gain access of website.      
    2. The response consists two cookies - JWT_TOKEN and AUTHENTICATION_TOKEN. Keep JWT_TOKEN as it is, read AUTHENTICATION_TOKEN and set Authorization token as "Token + (value of token)".
****
           
#### Verification of Email Address

```http
  POST /api/v1/user/verify_email/
```
**All parameters are required**
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `otp`      | `string` | OTP sent on email address. |

****
#### Login the User

```http
  POST /api/v1/user/login/
```
**All parameters are required**
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `user_name`      | `string` | Username of the user. |
| `password`      | `string` | Raw password of the user. |

**Steps to follow after successful log-in of account :**   
    The response consists two cookies - JWT_TOKEN and AUTHENTICATION_TOKEN. Keep JWT_TOKEN as it is, read AUTHENTICATION_TOKEN and set Authorization token as "Token + (value of token)".
****

#### Logout the User

```http
  GET /api/v1/user/logout/
```
**No parameters required.**
****

#### Get Degrees 
This URL needs to be called during adding educational details of the users. 
Call to this __doesn't__ need user to be logged-in.

```http
  GET /api/v1/user/get/degrees/
```
**No Parameters required.**

### Sample Output : 
```
{
  "degrees": [
    {
      "degree": "Associate Degree",
      "degree_id": 1
    },
    {
      "degree": "Bachelor Degree",
      "degree_id": 2
    },
    {
      "degree": "Diploma",
      "degree_id": 3
    }
}
```

****
## Educational Details
****

#### Insert educational details 

```http
  POST user/add/educational_details/
```
Users are required to be Logged-in.   \
 **All parameters are required.**
| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `institute` | `string` | example: "Modern College of Engineering" |
| `location` | `string` | example: "Pune" |
| `enrollment_year` | `integer` |example: 2021 |
| `completion_year` | `integer` | example: 2024 |
| `degree` | `integer` | example: Degree ID from get/degrees/ |
| `stream` | `string` | example: "Information Technology" |
| `grade` | `string` | example: Any string, Any Number (NOT REQUIRED)| 

Sample Input: 
  ```
 {
	"educational_data": [
	{
		"institute": "Modern College of Engineering, Pune",
		"location": "Pune, Maharashtra",
		"enrollment_year": "2021",
		"completion_year": "2024",
		"degree": "2",
		"stream": "Information Technology",
		"grade": "8.7"
	},
	{
		"institute": "Government Polytechnic, Pune",
		"location": "Pune, Maharashtra",
		"enrollment_year": "2018",
		"completion_year": "2021",
		"degree": "3",
		"stream": "Computer Engineering",
		"grade": "93.8"
	}]
}
  ```
Output: A 200 response on OK, and 406 on error.
****
#### Get Educational Details 
This URL needs to be called for getting educational details of the users. 
Call to this needs user to be logged-in.

```http
  GET /api/v1/user/get/educational_details/
```
**No Parameters required.**

### Sample Output : 
```
{
    "educational_details": [
        {
            "education_id": "e42a557c-4846-41bd-93f5-25c4a8e2a24f",
            "institute": "Government Polytechnic, Pune",
            "location": "Pune, Maharashtra",
            "enrollment_year": 2018,
            "completion_year": 2021,
            "degree": "Diploma",
            "stream": "Computer Engineering",
            "grade": "93.8",
            "user_id": "21e8ccd8-44b9-4e08-ab4f-e0546d56de3b"
        },
        {
            "education_id": "c06cace5-69d8-4ae4-9202-c1e9a019c213",
            "institute": "Modern College of Engineering, Pune",
            "location": "Pune, Maharashtra",
            "enrollment_year": 2021,
            "completion_year": 2024,
            "degree": "Bachelor Degree",
            "stream": "Information Technology",
            "grade": "8.7",
            "user_id": "21e8ccd8-44b9-4e08-ab4f-e0546d56de3b"
        }
    ]
}
```



## Authors

- [@SarveshJoshi25: Backend Developer](https://www.github.com/SarveshJoshi25)
- [@dhananjaykuber: Frontend Developer](https://www.github.com/dhananjaykuber)


## 🚀 About Me
Hello, I'm Sarvesh Joshi. Currently pursuing B.E. in Information Technology at Modern College of Engineering, Pune, and will be graduating in 2024.

I'm very passionate about Real-world software solutions. I've built several Backend APIs using Python Frameworks like Django and Flask, and I'm fluent in SQL Databases like MySQL, PostgreSQL, Oracle, etc., and NoSQL database MongoDB. I've deployed multiple projects using Heroku. Apart from Backend Development, I'm interested in Machine Learning and Data Science. I'm a Practioner of Competitive Programming, and I regularly participate in Competitive Coding Competitions on platforms like LeetCode and Codechef.

I Interned at RhythmFlows Solutions for 3 months, where I was responsible for API Development (Django, PostgreSQL).

I follow activities happening in the Indian Startup Ecosystem. I'm curious about different technologies and hence love the dynamic nature of Startups.

## 👋 Connect with me on  
[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/sarvesh-s-joshi/)
[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/_sarveshjoshi)


