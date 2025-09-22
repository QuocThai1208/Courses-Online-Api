# Backend - Courses Online API

Hệ thống Backend cho nền tảng khóa học trực tuyến, xây dựng bằng Django REST Framework.

## Chức năng chính
- Quản lý danh mục (Category)
- Quản lý khóa học (Course), chương (Chapter), bài học (Lesson)
- Đăng ký người dùng (Học viên/ Giảng viên), cập nhật hồ sơ, lấy thông tin người dùng hiện tại
- Ghi danh khóa học, thanh toán MoMo IPN
- Diễn đàn khóa học (Forum) với Topic, Comment, Reply
- Theo dõi tiến độ học (Lesson Progress, Course Progress)

## Xác thực & Phân quyền
- Sử dụng OAuth2 cho authentication (Endpoint cấp token: `/o/token/`)
- Sử dụng Bearer Token cho các request cần xác thực
- Phân quyền theo vai trò: Admin, Teacher, Student (custom permissions `IsAdmin`, `IsTeacher`, `IsStudent`, `IsTeacherOrAdmin`)

## Các API chính (prefix theo router)
- `GET /categories/`: Danh sách danh mục
- `GET /teachers/`: Dan sách giảng viên
- `GET /courses/`: Dan sách khóa học (lọc theo `lecturer`, `category`, `min_price`, `max_price`, `level`)
- `GET /courses/{id}/detail/`: Chi tiết khóa học (tối ưu quan hệ)
- `GET /courses/top/`: Top khóa học theo số lượng học viên
- `GET /courses/{id}/forum/`: Lấy forum của khóa học
- `GET|POST|PUT|PATCH|DELETE /chapters/`, `/lessons/`: Quản lý chương, bài học (giảng viên/ admin)
- `POST /users/register-student/`: Đăng ký học viên
- `POST /users/register-teacher/`: Đăng ký giảng viên
- `GET|PATCH /users/current-user/`: Lấy/ cập nhật thông tin người dùng hiện tại
- `GET /enrollments/`: Danh sách ghi danh (của chính user hoặc tất cả nếu admin)
- `POST /enrollments/create/`: Ghi danh khóa học, trả về `payUrl` MoMo
- `POST /payment/momo/ipn/`: IPN từ MoMo để cập nhật trạng thái thanh toán và ghi danh
- `GET|POST /forums/`: Danh sách/ tạo forum theo quyền (Teacher/Admin/Student đã ghi danh)
- `GET|POST|PUT|PATCH|DELETE /topics/`: Quản lý topic; `POST /topics/{id}/increment-view/` tăng lượt xem; `GET /topics/{id}/comments/` lấy bình luận
- `GET|POST|PUT|PATCH|DELETE /comments/`: Quản lý bình luận; `GET /comments/{id}/replies/` lấy danh sách reply
- `GET|POST|PUT|PATCH|DELETE /lesson-progress/`: Theo dõi tiến độ bài học
- `POST /lesson-progress/update-progress/`: Cập nhật tiến độ bài học
- `GET /lesson-progress/course/{course_id}/`: Lấy tiến độ toàn khóa học
- `GET /enrolled-courses/`: Danh sách khóa học đã ghi danh của user (kèm progress)

## Cách lấy Access Token (OAuth2)
- Endpoint: `POST /o/token/`
- Form fields thường dùng: `grant_type=password`, `username`, `password`, `client_id`, `client_secret`
- Sau khi lấy được `access_token`, gửi kèm header `Authorization: Bearer <token>` cho các API yêu cầu xác thực

## Tài khoản test
- Username: `student1`
- Mật khẩu: `18072004@Hnt`

## Cài đặt & Chạy (local)
1) Tạo và kích hoạt virtualenv (Python 3.8+)
2) Cài dependencies:
```bash
pip install -r requirements.txt
```
3) Chạy migrate và khởi động server:
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
4) API sẽ chạy tại `http://localhost:8000/`

Lưu ý: Cấu hình OAuth2 (client_id/secret) cần được tạo theo hệ thống OAuth2 của dự án (django-oauth-toolkit). IPN MoMo cần cấu hình đúng URL `payment/momo/ipn/` để nhận thông báo.

