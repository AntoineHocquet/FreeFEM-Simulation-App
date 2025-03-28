%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% fichier = 'lecture_sllg.m'
% Description:
% Bowup de Landau Lifshitz Stochastique
% Se lit apres execution du script Freefem++ sllg.edp
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
clear all;
close all;
clc;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%% parametres d'affichage %%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
G=[];l=1;scale=5;avec_pause=0;carre=0;point_de_vue=[6 6 1];
figure(1)
aviobj=avifile('sllg1.avi','fps',22)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%% recuperation donnees %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
fid=fopen(['parameters_u.txt'],'r');mat=fscanf(fid,'%f',[2 1])';
fclose(fid);T=mat(1);N=mat(2);
ffid=fopen(['iter.txt'],'r');mmat=fscanf(ffid,'%f',[2 1])';
Niter=mmat(1);Titer=mmat(2);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%% construction donnees complementaires %%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
dt=T/N;E1=[];
%construction du disque vert (pour les graphiques)
theta=0:0.11:2*pi;r=0:0.1:1;[THETA,R]=meshgrid(theta,r);
disk1=R.*cos(THETA);disk2=R.*sin(THETA);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%lecture des donnees avec quiver3 %%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
scale=4;
l=1;
for n=0:Niter-1
    % 1ere trajectoire
    fid=fopen(['u/u4/valU/u_' num2str(n) '.txt'],'r');X=fscanf(fid,'%f',[9 inf])';
    x1=X(:,1);y1=X(:,2);z=X(:,3);u0_1=X(:,4);u1_1=X(:,5);u2_1=X(:,6);
    h=X(:,7);Edensity1=X(:,8);E1(n+1)=X(1,9);
    fclose(fid);
    Emax1(n+1)=max(Edensity1);
    % 2e trajectoire
    fid=fopen(['u/u1/valU/u_' num2str(n) '.txt'],'r');X=fscanf(fid,'%f',[9 inf])';
    x2=X(:,1);y2=X(:,2);z2=X(:,3);u0_2=X(:,4);u1_2=X(:,5);u2_2=X(:,6);
    h=X(:,7);Edensity2=X(:,8);E2(n+1)=X(1,9);
    fclose(fid);
    Emax2(n+1)=max(Edensity2);
    % 3e trajectoire
    fid=fopen(['u/u7/valU/u_' num2str(n) '.txt'],'r');X=fscanf(fid,'%f',[9 inf])';
    x3=X(:,1);y3=X(:,2);z3=X(:,3);u0_3=X(:,4);u1_3=X(:,5);u2_3=X(:,6);
    h=X(:,7);Edensity3=X(:,8);E3(n+1)=X(1,9);
    fclose(fid);
    Emax3(n+1)=max(Edensity3);
    % 1ere trajectoire
    fid=fopen(['u/u4/valU/u_' num2str(n) '.txt'],'r');X=fscanf(fid,'%f',[9 inf])';
    x1=X(:,1);y1=X(:,2);z=X(:,3);u0_1=X(:,4);u1_1=X(:,5);u2_1=X(:,6);
    h=X(:,7);Edensity1=X(:,8);E1(n+1)=X(1,9);
    fclose(fid);
    % affichage d'une trajectoire
    u0=u0_2;u1=u1_2;u2=u2_2;x=x2;y=y2;
    indices1=find(u2>0);indices0=find(u2<=0);nn=0.1;
    quiver(x(indices1),y(indices1),nn*u0(indices1),nn*u1(indices1),0,'red');hold on;
    quiver(x(indices0),y(indices0),nn*u0(indices0),nn*u1(indices0),0,'blue');hold off;
    title(['t = ' num2str(dt*n)]);
    G=getframe;
    %pause
    %quiver3(x1(1:l:end),y1(1:l:end),z(1:l:end),...
    %    u0_1(1:l:end),u1_1(1:l:end),u2_1(1:l:end),scale);hold on;
    %    mesh(disk1,disk2,0*disk1);hold off;
    %view(point_de_vue);axis([-1 1 -1 1 -1 1]);
%scatter(x1,y1,9,u2_1,'*');hold off;
end;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
close all;
tt=linspace(0,T,Niter); % intervalle de temps
plot(tt,E1,tt,E2,tt,E3)
axis([0 T 0 max([max(E1) max(E2) max(E3)])]) % Energie totale
legend('\omega_1','\omega_2','\omega_3')
pause
close all;
plot(tt,Emax1,tt,Emax2,tt,Emax3) % Norme infinie Edensity
axis([0 T 0 max([max(Emax1) max(Emax2) max(Emax3)])])
legend('\omega_1','\omega_2','\omega_3')