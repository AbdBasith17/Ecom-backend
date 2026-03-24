from rest_framework_simplejwt.tokens import RefreshToken

class CustomRefreshToken(RefreshToken):

    @classmethod
    def for_user(cls, user):
        refresh = super().for_user(user)

        
        refresh["user_id"] = user.id
        refresh["email"] = user.email
        refresh["name"] = user.name
        refresh["role"] = user.role

       
        access = refresh.access_token
        access["user_id"] = user.id
        access["email"] = user.email
        access["role"] = user.role

        return refresh
