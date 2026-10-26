# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'catphan_worksheet.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_QCatPhanWorksheet(object):
    def setupUi(self, QCatPhanWorksheet):
        if not QCatPhanWorksheet.objectName():
            QCatPhanWorksheet.setObjectName(u"QCatPhanWorksheet")
        QCatPhanWorksheet.resize(1237, 552)
        self.verticalLayout = QVBoxLayout(QCatPhanWorksheet)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.stackedWidget = QStackedWidget(QCatPhanWorksheet)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.analysisPage = QWidget()
        self.analysisPage.setObjectName(u"analysisPage")
        self.gridLayout = QGridLayout(self.analysisPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(20)
        self.frame_2 = QFrame(self.analysisPage)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy1)
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, -1)
        self.line = QFrame(self.frame_2)
        self.line.setObjectName(u"line")
        self.line.setMaximumSize(QSize(16777215, 1))
        self.line.setStyleSheet(u"background-color: rgb(82, 142, 122)")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.configFormLayout = QFormLayout()
        self.configFormLayout.setObjectName(u"configFormLayout")
        self.phantomLabel = QLabel(self.frame_2)
        self.phantomLabel.setObjectName(u"phantomLabel")

        self.configFormLayout.setWidget(0, QFormLayout.LabelRole, self.phantomLabel)

        self.phantomCB = QComboBox(self.frame_2)
        self.phantomCB.setObjectName(u"phantomCB")

        self.configFormLayout.setWidget(0, QFormLayout.FieldRole, self.phantomCB)

        self.huToleranceLabel = QLabel(self.frame_2)
        self.huToleranceLabel.setObjectName(u"huToleranceLabel")

        self.configFormLayout.setWidget(1, QFormLayout.LabelRole, self.huToleranceLabel)

        self.huToleranceDSB = QDoubleSpinBox(self.frame_2)
        self.huToleranceDSB.setObjectName(u"huToleranceDSB")
        self.huToleranceDSB.setDecimals(0)
        self.huToleranceDSB.setMinimum(1.000000000000000)
        self.huToleranceDSB.setMaximum(500.000000000000000)
        self.huToleranceDSB.setSingleStep(5.000000000000000)
        self.huToleranceDSB.setValue(40.000000000000000)

        self.configFormLayout.setWidget(1, QFormLayout.FieldRole, self.huToleranceDSB)

        self.scalingToleranceLabel = QLabel(self.frame_2)
        self.scalingToleranceLabel.setObjectName(u"scalingToleranceLabel")

        self.configFormLayout.setWidget(2, QFormLayout.LabelRole, self.scalingToleranceLabel)

        self.scalingToleranceDSB = QDoubleSpinBox(self.frame_2)
        self.scalingToleranceDSB.setObjectName(u"scalingToleranceDSB")
        self.scalingToleranceDSB.setDecimals(2)
        self.scalingToleranceDSB.setMinimum(0.050000000000000)
        self.scalingToleranceDSB.setMaximum(10.000000000000000)
        self.scalingToleranceDSB.setSingleStep(0.100000000000000)
        self.scalingToleranceDSB.setValue(1.000000000000000)

        self.configFormLayout.setWidget(2, QFormLayout.FieldRole, self.scalingToleranceDSB)

        self.thicknessToleranceLabel = QLabel(self.frame_2)
        self.thicknessToleranceLabel.setObjectName(u"thicknessToleranceLabel")

        self.configFormLayout.setWidget(3, QFormLayout.LabelRole, self.thicknessToleranceLabel)

        self.thicknessToleranceDSB = QDoubleSpinBox(self.frame_2)
        self.thicknessToleranceDSB.setObjectName(u"thicknessToleranceDSB")
        self.thicknessToleranceDSB.setDecimals(2)
        self.thicknessToleranceDSB.setMinimum(0.010000000000000)
        self.thicknessToleranceDSB.setMaximum(5.000000000000000)
        self.thicknessToleranceDSB.setSingleStep(0.050000000000000)
        self.thicknessToleranceDSB.setValue(0.200000000000000)

        self.configFormLayout.setWidget(3, QFormLayout.FieldRole, self.thicknessToleranceDSB)

        self.lowContrastToleranceLabel = QLabel(self.frame_2)
        self.lowContrastToleranceLabel.setObjectName(u"lowContrastToleranceLabel")

        self.configFormLayout.setWidget(4, QFormLayout.LabelRole, self.lowContrastToleranceLabel)

        self.lowContrastToleranceSB = QSpinBox(self.frame_2)
        self.lowContrastToleranceSB.setObjectName(u"lowContrastToleranceSB")
        self.lowContrastToleranceSB.setMinimum(0)
        self.lowContrastToleranceSB.setMaximum(20)
        self.lowContrastToleranceSB.setValue(1)

        self.configFormLayout.setWidget(4, QFormLayout.FieldRole, self.lowContrastToleranceSB)

        self.cnrThresholdLabel = QLabel(self.frame_2)
        self.cnrThresholdLabel.setObjectName(u"cnrThresholdLabel")

        self.configFormLayout.setWidget(5, QFormLayout.LabelRole, self.cnrThresholdLabel)

        self.cnrThresholdDSB = QDoubleSpinBox(self.frame_2)
        self.cnrThresholdDSB.setObjectName(u"cnrThresholdDSB")
        self.cnrThresholdDSB.setDecimals(1)
        self.cnrThresholdDSB.setMaximum(200.000000000000000)
        self.cnrThresholdDSB.setSingleStep(1.000000000000000)
        self.cnrThresholdDSB.setValue(15.000000000000000)

        self.configFormLayout.setWidget(5, QFormLayout.FieldRole, self.cnrThresholdDSB)

        self.contrastMethodLabel = QLabel(self.frame_2)
        self.contrastMethodLabel.setObjectName(u"contrastMethodLabel")

        self.configFormLayout.setWidget(6, QFormLayout.LabelRole, self.contrastMethodLabel)

        self.contrastMethodCB = QComboBox(self.frame_2)
        self.contrastMethodCB.setObjectName(u"contrastMethodCB")

        self.configFormLayout.setWidget(6, QFormLayout.FieldRole, self.contrastMethodCB)

        self.visibilityThresholdLabel = QLabel(self.frame_2)
        self.visibilityThresholdLabel.setObjectName(u"visibilityThresholdLabel")

        self.configFormLayout.setWidget(7, QFormLayout.LabelRole, self.visibilityThresholdLabel)

        self.visibilityThresholdDSB = QDoubleSpinBox(self.frame_2)
        self.visibilityThresholdDSB.setObjectName(u"visibilityThresholdDSB")
        self.visibilityThresholdDSB.setDecimals(3)
        self.visibilityThresholdDSB.setMaximum(10.000000000000000)
        self.visibilityThresholdDSB.setSingleStep(0.010000000000000)
        self.visibilityThresholdDSB.setValue(0.150000000000000)

        self.configFormLayout.setWidget(7, QFormLayout.FieldRole, self.visibilityThresholdDSB)

        self.originSliceLabel = QLabel(self.frame_2)
        self.originSliceLabel.setObjectName(u"originSliceLabel")

        self.configFormLayout.setWidget(8, QFormLayout.LabelRole, self.originSliceLabel)

        self.originSliceSB = QSpinBox(self.frame_2)
        self.originSliceSB.setObjectName(u"originSliceSB")
        self.originSliceSB.setMinimum(-1)
        self.originSliceSB.setMaximum(2000)
        self.originSliceSB.setValue(-1)

        self.configFormLayout.setWidget(8, QFormLayout.FieldRole, self.originSliceSB)


        self.verticalLayout_4.addLayout(self.configFormLayout)

        self.verticalSpacer_6 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_4.addItem(self.verticalSpacer_6)

        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(13)
        self.label_2.setFont(font)

        self.verticalLayout_4.addWidget(self.label_2)

        self.line_3 = QFrame(self.frame_2)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setMaximumSize(QSize(16777215, 1))
        self.line_3.setStyleSheet(u"background-color: rgb(82, 142, 122)")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line_3)

        self.outcomeLE = QLineEdit(self.frame_2)
        self.outcomeLE.setObjectName(u"outcomeLE")
        self.outcomeLE.setMinimumSize(QSize(250, 0))
        self.outcomeLE.setContextMenuPolicy(Qt.NoContextMenu)
        self.outcomeLE.setStyleSheet(u"border-color: rgb(95, 200, 26);\n"
"border-radius: 15px;\n"
"border-style: solid;\n"
"border-width: 2px;\n"
"background-color: rgba(95, 200, 26,150);\n"
"padding-left: 15px;\n"
"height: 30px;\n"
"font-weight: bold;\n"
"\n"
"")
        self.outcomeLE.setReadOnly(True)

        self.verticalLayout_4.addWidget(self.outcomeLE)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_5)


        self.gridLayout.addWidget(self.frame_2, 1, 3, 1, 1)

        self.mainActionsHL = QHBoxLayout()
        self.mainActionsHL.setSpacing(10)
        self.mainActionsHL.setObjectName(u"mainActionsHL")
        self.analyzeBtn = QPushButton(self.analysisPage)
        self.analyzeBtn.setObjectName(u"analyzeBtn")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.analyzeBtn.sizePolicy().hasHeightForWidth())
        self.analyzeBtn.setSizePolicy(sizePolicy2)
        self.analyzeBtn.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(82, 142, 122);\n"
"    min-width: 150px;\n"
"	min-height:20px;\n"
"    padding: 6px;\n"
"	border-radius: 15px;\n"
"	color: white;\n"
"	font: bold;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"	background-color: rgb(52, 91, 78);\n"
"}\n"
"\n"
"QPushButton:!enabled{\n"
"	background-color: rgba(52, 91, 78, 50);\n"
"	color: rgba(255,255,255,100)\n"
"}")

        self.mainActionsHL.addWidget(self.analyzeBtn, 0, Qt.AlignLeft)

        self.genReportBtn = QPushButton(self.analysisPage)
        self.genReportBtn.setObjectName(u"genReportBtn")
        sizePolicy2.setHeightForWidth(self.genReportBtn.sizePolicy().hasHeightForWidth())
        self.genReportBtn.setSizePolicy(sizePolicy2)
        self.genReportBtn.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(82, 142, 122);\n"
"    min-width: 150px;\n"
"	min-height:20px;\n"
"    padding: 6px;\n"
"	border-radius: 15px;\n"
"	color: white;\n"
"	font: bold;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"	background-color: rgb(52, 91, 78);\n"
"}\n"
"\n"
"QPushButton:!enabled{\n"
"	background-color: rgba(52, 91, 78, 50);\n"
"	color: rgba(255,255,255,100)\n"
"}")

        self.mainActionsHL.addWidget(self.genReportBtn, 0, Qt.AlignLeft)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.mainActionsHL.addItem(self.horizontalSpacer)


        self.gridLayout.addLayout(self.mainActionsHL, 2, 1, 1, 1)

        self.frame = QFrame(self.analysisPage)
        self.frame.setObjectName(u"frame")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy3)
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout_3 = QVBoxLayout(self.frame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, -1, -1)
        self.analysisSummaryLabel = QFrame(self.frame)
        self.analysisSummaryLabel.setObjectName(u"analysisSummaryLabel")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.analysisSummaryLabel.sizePolicy().hasHeightForWidth())
        self.analysisSummaryLabel.setSizePolicy(sizePolicy4)
        self.analysisSummaryLabel.setMaximumSize(QSize(16777215, 1))
        self.analysisSummaryLabel.setStyleSheet(u"background-color: rgb(82, 142, 122)")
        self.analysisSummaryLabel.setFrameShape(QFrame.Shape.HLine)
        self.analysisSummaryLabel.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.analysisSummaryLabel)

        self.buttonSpacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_3.addItem(self.buttonSpacer)

        self.analysisInfoVL = QVBoxLayout()
        self.analysisInfoVL.setObjectName(u"analysisInfoVL")

        self.verticalLayout_3.addLayout(self.analysisInfoVL)

        self.analysisImageVL = QVBoxLayout()
        self.analysisImageVL.setObjectName(u"analysisImageVL")

        self.verticalLayout_3.addLayout(self.analysisImageVL)

        self.image_vl_spacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding)

        self.verticalLayout_3.addItem(self.image_vl_spacer)


        self.gridLayout.addWidget(self.frame, 1, 1, 1, 1)

        self.importedImgLabel = QLabel(self.analysisPage)
        self.importedImgLabel.setObjectName(u"importedImgLabel")
        self.importedImgLabel.setFont(font)

        self.gridLayout.addWidget(self.importedImgLabel, 0, 0, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_3, 1, 4, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label = QLabel(self.analysisPage)
        self.label.setObjectName(u"label")
        sizePolicy3.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy3)
        self.label.setFont(font)

        self.horizontalLayout_3.addWidget(self.label, 0, Qt.AlignLeft)


        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 3, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.analysisSumLabel = QLabel(self.analysisPage)
        self.analysisSumLabel.setObjectName(u"analysisSumLabel")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.analysisSumLabel.sizePolicy().hasHeightForWidth())
        self.analysisSumLabel.setSizePolicy(sizePolicy5)
        self.analysisSumLabel.setFont(font)

        self.horizontalLayout_2.addWidget(self.analysisSumLabel)


        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)

        self.imageListWidget = QListWidget(self.analysisPage)
        self.imageListWidget.setObjectName(u"imageListWidget")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Expanding)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.imageListWidget.sizePolicy().hasHeightForWidth())
        self.imageListWidget.setSizePolicy(sizePolicy6)
        self.imageListWidget.setMinimumSize(QSize(350, 0))
        self.imageListWidget.setMaximumSize(QSize(350, 16777215))
        self.imageListWidget.setDragDropMode(QAbstractItemView.DragDrop)
        self.imageListWidget.setDefaultDropAction(Qt.MoveAction)
        self.imageListWidget.setAlternatingRowColors(True)

        self.gridLayout.addWidget(self.imageListWidget, 1, 0, 1, 1)

        self.addImgBtn = QPushButton(self.analysisPage)
        self.addImgBtn.setObjectName(u"addImgBtn")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.addImgBtn.sizePolicy().hasHeightForWidth())
        self.addImgBtn.setSizePolicy(sizePolicy7)
        self.addImgBtn.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(82, 142, 122);\n"
"    min-width: 150px;\n"
"	min-height:20px;\n"
"    padding: 6px;\n"
"	border-radius: 15px;\n"
"	color: white;\n"
"	font: bold;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"	background-color: rgb(52, 91, 78);\n"
"}\n"
"\n"
"QPushButton:!enabled{\n"
"	background-color: rgba(52, 91, 78, 50);\n"
"	color: rgba(255,255,255,100)\n"
"}")
        self.addImgBtn.setAutoDefault(False)

        self.gridLayout.addWidget(self.addImgBtn, 2, 0, 1, 1, Qt.AlignVCenter)

        self.line_2 = QFrame(self.analysisPage)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 1, 2, 1, 1)

        self.stackedWidget.addWidget(self.analysisPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(QCatPhanWorksheet)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(QCatPhanWorksheet)
    # setupUi

    def retranslateUi(self, QCatPhanWorksheet):
        QCatPhanWorksheet.setWindowTitle(QCoreApplication.translate("QCatPhanWorksheet", u"Form", None))
        self.phantomLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Phantom:", None))
        self.huToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"HU tolerance:", None))
        self.huToleranceDSB.setSuffix(QCoreApplication.translate("QCatPhanWorksheet", u" HU", None))
        self.scalingToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Scaling tolerance:", None))
        self.scalingToleranceDSB.setSuffix(QCoreApplication.translate("QCatPhanWorksheet", u" mm", None))
        self.thicknessToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Slice thickness tolerance:", None))
        self.thicknessToleranceDSB.setSuffix(QCoreApplication.translate("QCatPhanWorksheet", u" mm", None))
        self.lowContrastToleranceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Low-contrast ROIs required:", None))
        self.cnrThresholdLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"CNR threshold:", None))
        self.contrastMethodLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Contrast method:", None))
        self.visibilityThresholdLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Visibility threshold:", None))
        self.originSliceLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Origin slice:", None))
        self.originSliceSB.setSpecialValueText(QCoreApplication.translate("QCatPhanWorksheet", u"Auto", None))
        self.label_2.setText(QCoreApplication.translate("QCatPhanWorksheet", u"<html><head/><body><p><span style=\" font-weight:700;\">Analysis Outcome</span></p></body></html>", None))
        self.outcomeLE.setPlaceholderText(QCoreApplication.translate("QCatPhanWorksheet", u"N/A", None))
        self.analyzeBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Analyze CT series", None))
        self.genReportBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Generate report", None))
        self.importedImgLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Imported CT series", None))
        self.label.setText(QCoreApplication.translate("QCatPhanWorksheet", u"<html><head/><body><p><span style=\" font-weight:700;\">Configuration</span></p></body></html>", None))
        self.analysisSumLabel.setText(QCoreApplication.translate("QCatPhanWorksheet", u"<html><head/><body><p><span style=\" font-weight:700;\">Analysis summary</span></p></body></html>", None))
        self.addImgBtn.setText(QCoreApplication.translate("QCatPhanWorksheet", u"Add CT series", None))
    # retranslateUi

