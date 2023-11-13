import { NextApiRequest, NextApiResponse } from "next";
import { prisma } from "@/lib/prisma";
import type { ApiRes } from "@/types/api";
import { Project } from "@/types/projects";
import { getUserInfoFromSessionToken } from "@/lib/auth";

type PrismaProjectRecord = {
  id: string;
  name: string;
  description: string | null;
  tags: string | null;
  isActive: boolean;
  createdBy: string;
  createdAt: Date;
};

const processTags = (project: PrismaProjectRecord): Project => {
  return {
    ...project,
    tags: project.tags?.split(",").map((tag) => tag?.trim()) || [],
  };
};

const handler = async (
  req: NextApiRequest,
  res: NextApiResponse<ApiRes<Project>>
) => {
  const sessionToken = req.headers.sessiontoken as string;
  const user = await getUserInfoFromSessionToken(sessionToken);

  switch (req.method) {
    case "GET":
      const id = req.query.projectId as string;

      const project = await prisma.project.findFirst({
        where: {
          id: id,
          UserRole: {
            some: {
              userId: user?.id,
            },
          },
        },
      });

      if (!project)
        return res.status(404).json({
          success: false,
          error: "Project not found",
        });

      res.status(200).json({
        success: true,
        data: processTags(project),
      });
      break;

    default:
      res.status(405).json({
        success: true,
        error: "Method not allowed",
      });
      break;
  }
};

export default handler;