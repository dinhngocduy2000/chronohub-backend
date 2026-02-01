from app.common.exceptions.decorator import exception_handler
from app.common.schemas.user import UserCreate, UserInfo, UserLogin, UserLoginResponse
from app.services.auth import AuthService


class AuthHandler:
    service: AuthService

    def __init__(self, service: AuthService) -> None:
        self.service = service

    @exception_handler
    async def authenticate_user(self, login_request: UserLogin) -> UserLoginResponse:
        """
        Login a user

        Args:
            login_request: User login data including email and password

        Returns:
            UserLoginResponse: User login response
        """
        return await self.service.login_user(login_request)

    @exception_handler
    async def register_user(self, user_create: UserCreate) -> UserInfo:
        """
        Create a new user account

        Args:
            user_data: User registration data including email, name, and password

        Returns:
            UserInfo: Created user information

        Raises:
            BadRequestException: If email already exists or validation fails
        """
        return await self.service.create_user(user_create)
