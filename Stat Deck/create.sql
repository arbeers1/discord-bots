CREATE TABLE IF NOT EXISTS Users (
    Guild_Id INTEGER,
    User_Id INTEGER,
    Steam_ID INTEGER,
    PRIMARY KEY (Guild_Id, User_Id)
);