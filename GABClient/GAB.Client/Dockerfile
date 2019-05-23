FROM microsoft/dotnet:2.2-aspnetcore-runtime AS base
WORKDIR /app
EXPOSE 80

# Update
RUN apt-get update
RUN apt-get install -y python
RUN apt-get install -y python3 
RUN apt-get install -y python-pip
RUN apt-get install -y python-tk
RUN apt-get install -y libeigen3-dev
RUN apt-get install -y python3-pip

 
# Install app dependencies
RUN pip install --upgrade pip
#RUN pip install --trusted-host pypi.python.org -r requirements.txt
# Install pipeline 1 dependencies
RUN pip install matplotlib
RUN pip install numpy
RUN pip install astropy
RUN pip install 'photutils==0.3.2'
RUN pip install statsmodels
RUN pip install scipy
RUN pip install 'george==0.2.1'

# Install pipeline 2 dependencies
RUN pip3 install numpy
RUN pip3 install scipy
RUN pip3 install sklearn
RUN pip3 install statsmodels
RUN pip3 install astropy

# Environment variables
ENV BatchClient__Email "johndoe@foo.com"
ENV BatchClient__Fullname "John Doe"
ENV BatchClient__TeamName "Global Azure Team"
ENV BatchClient__CompanyName "Global Azure Bootcamp Org."
ENV BatchClient__CountryCode "XX"
ENV BatchClient__LabKeyCode "THE-GAB-ORG"

FROM microsoft/dotnet:2.2-sdk AS build
WORKDIR /src
COPY ["GAB.Client/GAB.Client.csproj", "GAB.Client/"]
RUN dotnet restore "GAB.Client/GAB.Client.csproj"
COPY . .
WORKDIR "/src/GAB.Client"
RUN dotnet build "GAB.Client.csproj" -c Release -o /app

FROM build AS publish
RUN dotnet publish "GAB.Client.csproj" -c Release -o /app

FROM base AS final
WORKDIR /app
COPY --from=publish /app .
ENTRYPOINT ["dotnet", "GAB.Client.dll"]