from app.common.exceptions import BadRequestException
from app.common.exceptions.decorator import exception_handler
from app.services.user import UserService
from app.common.schemas.user import UserCreate, UserInfo


class UserHandler:
    service: UserService

    def __init__(self, service: UserService) -> None:
        self.service = service

    @exception_handler
    async def create_user(self, user_data: UserCreate) -> UserInfo:
        """
        Create a new user account
        
        Args:
            user_data: User registration data including email, name, and password
            
        Returns:
            UserInfo: Created user information
            
        Raises:
            BadRequestException: If email already exists or validation fails
        """
        return await self.service.create_user(user_data)
